# -*- coding: utf-8 -*-
import asyncio
import json
import ssl
import time
import typing
from asyncio import TimeoutError

from tornado.httpclient import AsyncHTTPClient, HTTPResponse

from .Exceptions import AsyncyError, K8sError
from .Stories import Stories
from .constants.LineConstants import LineConstants
from .entities.Volume import Volume, Volumes
from .utils.HttpUtils import HttpUtils


class Kubernetes:

    @classmethod
    def is_2xx(cls, res: HTTPResponse):
        return int(res.code / 100) == 2

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
    async def create_namespace(cls, app):
        res = await cls.make_k8s_call(app,
                                      f'/api/v1/namespaces/{app.app_id}')

        if res.code == 200:
            app.logger.debug(f'Kubernetes namespace exists')
            return

        app.logger.debug(f'Kubernetes namespace does not exist')
        payload = {
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': app.app_id
            }
        }

        res = await cls.make_k8s_call(app, '/api/v1/namespaces',
                                      payload=payload)

        if not cls.is_2xx(res):
            raise K8sError('Failed to create namespace!')

        app.logger.debug(f'Kubernetes namespace created')

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

        if method.lower() == 'patch':
            kwargs['headers']['Content-Type'] = \
                'application/merge-patch+json; charset=utf-8'

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
        await cls._delete_resource(story.app, 'persistentvolumeclaims', name)

    @classmethod
    async def _does_resource_exist(cls, story, line, resource, name):
        prefix = cls._get_api_path_prefix(resource)
        path = f'{prefix}/{story.app.app_id}' \
               f'/{resource}/{name}'

        res = await cls.make_k8s_call(story.app, path)
        if res.code == 404:
            return False
        elif res.code == 200:
            return True

        raise K8sError(
            message=f'Failed to check if {resource}/{name} exists! '
                    f'Kubernetes API returned {res.code}.',
            story=story, line=line)

    @classmethod
    async def _update_volume_label(cls, story, line, app, name):
        path = f'/api/v1/namespaces/{app.app_id}/persistentvolumeclaims/{name}'
        payload = {
            'metadata': {
                'labels': {
                    'last_referenced_on': f'{int(time.time())}'
                }
            }
        }
        res = await cls.make_k8s_call(app, path, payload, method='patch')
        cls.raise_if_not_2xx(res, story, line)
        story.logger.debug(
            f'Updated reference time for volume {name}')

    @classmethod
    async def create_volume(cls, story, line, name, persist):
        if await cls._does_resource_exist(
                story, line, 'persistentvolumeclaims', name):
            story.logger.debug(f'Kubernetes volume {name} already exists')
            # Update the last_referenced_on label
            await cls._update_volume_label(story, line, story.app, name)
            return

        path = f'/api/v1/namespaces/{story.app.app_id}/persistentvolumeclaims'
        payload = {
            'apiVersion': 'v1',
            'kind': 'PersistentVolumeClaim',
            'metadata': {
                'name': name,
                'namespace': story.app.app_id,
                'labels': {
                    'last_referenced_on': f'{int(time.time())}',
                    'omg_persist': f'{persist}'
                }
            },
            'spec': {
                'accessModes': ['ReadWriteOnce'],
                'resources': {
                    'requests': {
                        'storage': '100Mi'  # For now, during beta.
                    }
                }
            }
        }

        res = await cls.make_k8s_call(story.app, path, payload)
        cls.raise_if_not_2xx(res, story, line)
        story.logger.debug(f'Created a Kubernetes volume - {name}')

    @classmethod
    def _get_api_path_prefix(cls, resource):
        if resource == 'deployments':
            return '/apis/apps/v1/namespaces'
        elif resource == 'services' or \
                resource == 'persistentvolumeclaims' or \
                resource == 'pods':
            return '/api/v1/namespaces'
        else:
            raise Exception(f'Unsupported resource type {resource}')

    @classmethod
    async def _list_resource_names(cls, app, resource) -> typing.List[str]:
        prefix = cls._get_api_path_prefix(resource)
        res = await cls.make_k8s_call(
            app, f'{prefix}/{app.app_id}/{resource}'
                 f'?includeUninitialized=true')

        body = json.loads(res.body, encoding='utf-8')
        out = []

        for i in body['items']:
            out.append(i['metadata']['name'])

        return out

    @classmethod
    async def _delete_resource(cls, app, resource, name):
        """
        Deletes a resource immediately.
        :param app: An instance of App
        :param resource: "services"/"deployments"/etc.
        :param name: The resource name
        """
        prefix = cls._get_api_path_prefix(resource)
        res = await cls.make_k8s_call(
            app,
            f'{prefix}/{app.app_id}/{resource}/{name}'
            f'?gracePeriodSeconds=0',
            method='delete')

        if res.code == 404:
            app.logger.debug(f'Resource {resource}/{name} not found')
            return

        # Sometimes, the API will throw a 409, indicating that a
        # deletion is in progress. Don't assert that the status code
        # is 2xx in this case.
        if res.code != 409:
            cls.raise_if_not_2xx(res, None, None)

        # Wait until the resource has actually been killed.
        while True:
            res = await cls.make_k8s_call(
                app, f'{prefix}/{app.app_id}/{resource}/{name}')

            if res.code == 404:
                break

            app.logger.debug(f'{resource}/{name} is still terminating...')

            await asyncio.sleep(0.7)

        app.logger.debug(f'Deleted {resource}/{name} successfully!')

    @classmethod
    async def clean_namespace(cls, app):
        app.logger.debug(f'Clearing namespace contents...')
        # Things to delete:
        # 1. Services
        # 2. Deployments (should delete all pods internally too)
        # 3. Volumes which are marked with persist as false

        for i in await cls._list_resource_names(app, 'services'):
            await cls._delete_resource(app, 'services', i)

        for i in await cls._list_resource_names(app, 'deployments'):
            await cls._delete_resource(app, 'deployments', i)

        for i in await cls._list_resource_names(app, 'pods'):
            await cls._delete_resource(app, 'pods', i)

        # Volumes are not deleted at this moment.
        # See https://github.com/asyncy/platform-engine/issues/189

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
    def format_ports(cls, ports: {int}):
        port_list = []
        for port in ports:
            port_list.append({
                'port': port,
                'protocol': 'TCP',
                'targetPort': port
            })
        return port_list

    @classmethod
    async def create_service(cls, story: Stories, line: dict,
                             container_name: str):
        # Note: We don't check if this service exists because if it did,
        # then we'd not get here. create_pod checks it. During beta, we tie
        # 1:1 between a pod and a service.
        service = line[LineConstants.service]
        ports = cls.find_all_ports(story.app.services[service])
        port_list = cls.format_ports(ports)

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

        # Wait until the ports of the destination pod are open.
        hostname = cls.get_hostname(story, line, container_name)
        story.app.logger.info(f'Waiting for ports to open: {ports}')
        for port in ports:
            success = await cls.wait_for_port(hostname, port)
            if not success:
                story.app.logger.warn(
                    f'Timed out waiting for {hostname}:{port} to open. '
                    f'Some actions of {service} might fail!')

    @classmethod
    async def wait_for_port(cls, host, port):
        attempts = 0
        timeout_secs = 2
        while attempts < 60:  # Max wait time = attempts * timeout_secs = 120
            attempts += 1
            try:
                fut = asyncio.open_connection(host, port)
                await asyncio.wait_for(fut, timeout=timeout_secs)
                return True
            except (TimeoutError, ConnectionRefusedError):
                await asyncio.sleep(timeout_secs)

        return False

    @classmethod
    async def create_deployment(cls, story: Stories, line: dict, image: str,
                                container_name: str, start_command: [] or str,
                                shutdown_command: [] or str, env: dict,
                                volumes: Volumes):
        # Note: We don't check if this deployment exists because if it did,
        # then we'd not get here. create_pod checks it. During beta, we tie
        # 1:1 between a pod and a deployment.

        env_k8s = []  # Must container {name:'foo', value:'bar'}.

        if env:
            for k, v in env.items():
                env_k8s.append({
                    'name': k,
                    'value': v
                })

        volume_mounts = []
        volumes_k8s = []
        for vol in volumes:
            volume_mounts.append({
                'mountPath': vol.mount_path,
                'name': vol.name
            })

            volumes_k8s.append({
                'name': vol.name,
                'persistentVolumeClaim': {
                    'claimName': vol.name
                }
            })

            if not vol.persist:
                await cls.remove_volume(story, line, vol.name)

            await cls.create_volume(story, line, vol.name, vol.persist)

        payload = {
            'apiVersion': 'apps/v1',
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
                'selector': {
                    'matchLabels': {
                        'app': container_name
                    }
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
                                'resources': {
                                    'limits': {
                                        'memory': '100Mi',  # During beta.
                                        'cpu': '0.01',  # During beta.
                                    }
                                },
                                'command': start_command,
                                'imagePullPolicy': 'Always',
                                'env': env_k8s,
                                'lifecycle': {
                                },
                                'volumeMounts': volume_mounts
                            }
                        ],
                        'volumes': volumes_k8s
                    }
                }
            }
        }

        if shutdown_command is not None:
            payload['spec']['template']['spec']['containers'][0]['lifecycle'][
                'preStop'] = {
                'exec': {
                    'command': shutdown_command
                }
            }

        path = f'/apis/apps/v1/namespaces/{story.app.app_id}/deployments'

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

        path = f'/apis/apps/v1/namespaces/{story.app.app_id}' \
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
                         shutdown_command: [] or str, env: dict,
                         volumes: Volumes):
        res = await cls.make_k8s_call(
            story.app,
            f'/apis/apps/v1/namespaces/{story.app.app_id}'
            f'/deployments/{container_name}')

        if res.code == 200:
            story.logger.debug(f'Deployment {container_name} '
                               f'already exists, reusing')
            return

        await cls.create_deployment(story, line, image, container_name,
                                    start_command, shutdown_command, env,
                                    volumes)

        await cls.create_service(story, line, container_name)
