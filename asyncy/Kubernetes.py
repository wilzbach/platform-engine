# -*- coding: utf-8 -*-
import json

import asyncio
from tornado.httpclient import AsyncHTTPClient, HTTPResponse
import ssl

from .Exceptions import K8sError
from .Stories import Stories
from .utils.HttpUtils import HttpUtils


class Kubernetes:

    @classmethod
    def is_2xx(cls, res: HTTPResponse):
        return round(res.code / 100) == 2

    @classmethod
    def raise_if_not_2xx(cls, res: HTTPResponse, story, line):
        if cls.is_2xx(res):
            return

        path = res.request.url
        raise K8sError(story=story, line=line,
                       message=f'Failed to call {path}! '
                               f'code={res.code}; body={res.body}; '
                               f'error={res.error}')

    @classmethod
    async def create_namespace_if_required(cls, story, line):
        res = await cls.make_k8s_call(story.app,
                                      f'/api/v1/namespaces/{story.app.app_id}')

        if res.code == 200:
            story.logger.debug(f'k8s namespace {story.app.app_id} exists')
            return

        story.logger.debug(f'k8s namespace {story.app.app_id} does not exist')
        payload = {
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': story.app.app_id
            }
        }

        res = await cls.make_k8s_call(story.app, '/api/v1/namespaces',
                                      payload=payload)

        cls.raise_if_not_2xx(res, story, line)
        story.logger.debug(f'k8s namespace {story.app.app_id} created')

    @classmethod
    async def make_k8s_call(cls, app, path: str,
                            payload: dict = None,
                            method: str = 'get',
                            allow_nonstandard_methods=False) -> HTTPResponse:
        config = app.config

        context = ssl.SSLContext()

        # TODO: probably better to use the cafile here instead of doing this
        cert = config.CLUSTER_CERT
        cert = cert.replace('\\n', '\n')
        context.load_verify_locations(cadata=cert)

        kwargs = {
            'ssl_options': context,
            'headers': {
                'Authorization': f'bearer {config.CLUSTER_AUTH_TOKEN}',
                'Content-Type': 'application/json; charset=utf-8'
            },
            'allow_nonstandard_methods': allow_nonstandard_methods,
            'method': method.upper()
        }

        if payload is not None:
            kwargs['body'] = json.dumps(payload)

            if method == 'get':  # Default value.
                kwargs['method'] = 'POST'

        client = AsyncHTTPClient()
        return await HttpUtils.fetch_with_retry(
            3, app.logger, f'https://{app.config.CLUSTER_HOST}{path}',
            client, kwargs)

    @classmethod
    async def remove_volume(cls, story, line, name):
        pass

    @classmethod
    async def create_volume(cls, story, line, name):
        pass

    @classmethod
    async def remove_pod(cls, story, line, container):
        pass

    @classmethod
    async def clean_namespace(cls, app):
        app.logger.debug(f'Clearing namespace for app {app.app_id}')

        res = await cls.make_k8s_call(
            app,
            f'/api/v1/namespaces/{app.app_id}?PropagationPolicy=Foreground',
            method='delete')

        if res.code == 404:
            return

        cls.raise_if_not_2xx(res, None, None)

        # Wait until the namespace has actually been killed.
        while True:
            res = await cls.make_k8s_call(app,
                                          f'/api/v1/namespaces/{app.app_id}')

            if res.code == 404:
                break

            app.logger.debug(
                f'Namespace for app {app.app_id} is still terminating...')

            await asyncio.sleep(0.7)

        app.logger.debug(
            f'Cleared namespace for app {app.app_id} successfully')

    @classmethod
    def get_hostname(cls, story, line, container_name):
        # See
        # https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/
        return f'{container_name}.default-subdomain.' \
               f'{story.app.app_id}.svc.cluster.local'

    @classmethod
    async def create_pod(cls, story: Stories, line: dict, image: str,
                         container_name: str, start_command: [] or str,
                         env: dict):
        # TODO:  wait until the pod has actually started
        # TODO: create a deployment instead of just a pod
        await cls.create_namespace_if_required(story, line)
        res = await cls.make_k8s_call(
            story.app,
            f'/api/v1/namespaces/{story.app.app_id}/pods/{container_name}')

        if res.code == 200:
            story.logger.debug(f'Pod {container_name} '
                               f'already exists, reusing')
            return

        env_k8s = []

        if env:
            for k, v in env.items():
                env_k8s.append({
                    'name': k,
                    'value': v
                })
        payload = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'name': container_name,
                'namespace': story.app.app_id
            },
            'spec': {
                'hostname': container_name,
                'subdomain': 'default-subdomain',
                'containers': [
                    {
                        'name': container_name,
                        'image': image,
                        'command': start_command,
                        'env': env_k8s,
                        'lifecycle': {
                            'preStop': {
                                'exec': {
                                    'command': ['echo', 'todo']
                                }
                            }
                        }
                    }
                ]
            }
        }

        path = f'/api/v1/namespaces/{story.app.app_id}/pods'

        # When a namespace is created for the first time, K8s needs to perform
        # some sort of preparation. Pods creation fails sporadically for new
        # namespaces. Check the status and retry.
        tries = 0
        res = None
        while tries < 10:
            tries = tries + 1
            res = await cls.make_k8s_call(story.app, path, payload)
            if cls.is_2xx(res):
                break

            story.logger.debug(f'Failed to create pod, retrying...')
            await asyncio.sleep(1)

        cls.raise_if_not_2xx(res, story, line)
