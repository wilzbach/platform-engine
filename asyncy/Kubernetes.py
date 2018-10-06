# -*- coding: utf-8 -*-
import asyncio
import json
import ssl

from tornado.httpclient import AsyncHTTPClient, HTTPResponse

from .Exceptions import K8sError
from .Stories import Stories
from .constants.LineConstants import LineConstants
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
    def new_ssl_context(cls):
        return ssl.SSLContext()

    @classmethod
    async def make_k8s_call(cls, app, path: str,
                            payload: dict = None,
                            method: str = 'get') -> HTTPResponse:
        config = app.config

        context = cls.new_ssl_context()

        cert = config.CLUSTER_CERT
        cert = cert.replace('\\n', '\n')
        context.load_verify_locations(cadata=cert)

        kwargs = {
            'ssl_options': context,
            'headers': {
                'Authorization': f'bearer {config.CLUSTER_AUTH_TOKEN}',
                'Content-Type': 'application/json; charset=utf-8'
            },
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
        # TODO:
        pass

    @classmethod
    async def create_volume(cls, story, line, name):
        # TODO:
        pass

    @classmethod
    async def remove_pod(cls, story, line, container):
        # TODO:
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

        # Sometimes, the API will throw a 409, indicating that a
        # deletion is in progress. Don't assert that the status code
        # is 2xx in this case.
        if res.code != 409:
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
        return f'{container_name}.' \
               f'{story.app.app_id}.svc.cluster.local'

    @classmethod
    def find_all_ports(cls, service_config: dict, inside_http=False) -> set:
        ports = set()
        for key, value in service_config.items():
            if isinstance(value, dict):
                http = key == 'http' or inside_http
                ports.update(cls.find_all_ports(value, inside_http=http))
            elif inside_http and key == 'port':
                assert isinstance(value, int)
                ports.add(value)

        return ports

    @classmethod
    async def create_service(cls, story: Stories, line: dict,
                             container_name: str):
        # Note: We don't check if this service exists because if it did,
        # then we'd not get here. create_pod checks it. During beta, we tie
        # 1:1 between a pod and a service.
        service = line[LineConstants.service]
        ports = cls.find_all_ports(story.app.services[service])
        port_list = []
        for port in ports:
            port_list.append({
                'port': port,
                'protocol': 'TCP',
                'targetPort': port
            })

        payload = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': container_name,
                'namespace': story.app.app_id,
                'labels': {
                    'app': container_name
                }
            },
            'spec': {
                'ports': port_list,
                'selector': {
                    'app': container_name
                }
            }
        }

        path = f'/api/v1/namespaces/{story.app.app_id}/services'
        res = await cls.make_k8s_call(story.app, path, payload)
        cls.raise_if_not_2xx(res, story, line)
        await asyncio.sleep(2)  # todo: find a way to reliably decipher this.

    @classmethod
    async def create_deployment(cls, story: Stories, line: dict, image: str,
                                container_name: str, start_command: [] or str,
                                env: dict):
        # Note: We don't check if this deployment exists because if it did,
        # then we'd not get here. create_pod checks it. During beta, we tie
        # 1:1 between a pod and a deployment.

        env_k8s = []  # Must container {name:'foo', value:'bar'}.
        ports_k8s = []  # Must contain {name:'foo',containerPort:8080}.

        if env:
            for k, v in env.items():
                env_k8s.append({
                    'name': k,
                    'value': v
                })

        payload = {
            'apiVersion': 'apps/v1beta1',
            'kind': 'Deployment',
            'metadata': {
                'name': container_name,
                'namespace': story.app.app_id
            },
            'spec': {
                'replicas': 1,
                'strategy': {
                    'type': 'RollingUpdate'
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': container_name
                        }
                    },
                    'spec': {
                        'containers': [
                            {
                                'name': container_name,
                                'image': image,
                                'imagePullPolicy': 'Always',
                                'ports': ports_k8s,
                                'env': env_k8s,
                                'lifecycle': {
                                    'preStop': {
                                        'exec': {
                                            'command': ['echo', 'todo']  # todo
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }

        path = f'/apis/apps/v1beta1/namespaces/{story.app.app_id}/deployments'

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

            story.logger.debug(f'Failed to create deployment, retrying...')
            await asyncio.sleep(1)

        cls.raise_if_not_2xx(res, story, line)

        path = f'/apis/apps/v1beta1/namespaces/{story.app.app_id}' \
               f'/deployments/{container_name}'

        # Wait until the deployment is ready.
        while True:
            res = await cls.make_k8s_call(story.app, path)
            cls.raise_if_not_2xx(res, story, line)
            body = json.loads(res.body, encoding='utf-8')
            if body['status'].get('readyReplicas', 0) > 0:
                break

            story.logger.debug('Waiting for deployment to be ready...')
            await asyncio.sleep(1)

    @classmethod
    async def create_pod(cls, story: Stories, line: dict, image: str,
                         container_name: str, start_command: [] or str,
                         env: dict):
        await cls.create_namespace_if_required(story, line)
        res = await cls.make_k8s_call(
            story.app,
            f'/apis/apps/v1/namespaces/{story.app.app_id}'
            f'/deployments/{container_name}')

        if res.code == 200:
            story.logger.debug(f'Deployment {container_name} '
                               f'already exists, reusing')
            return

        await cls.create_deployment(story, line, image, container_name,
                                    start_command, env)

        await cls.create_service(story, line, container_name)
