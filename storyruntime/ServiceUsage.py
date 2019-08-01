import asyncio
import json
import urllib.parse
from typing import Dict, List, Tuple, Union

import numpy as np

from .Config import Config
from .Exceptions import K8sError
from .Kubernetes import Kubernetes
from .Logger import Logger
from .constants.ServiceConstants import ServiceConstants
from .db.Database import Database


class ServiceUsage:

    WAIT_PERIOD = 5 * 60
    BATCH_SIZE = 100

    @classmethod
    def split_value(cls, value: str,
                    suffix_len: int) -> Tuple[float, Union[str, None]]:
        suffix = value[-suffix_len:]
        if not suffix.isdigit():
            return float(value[:-suffix_len]), suffix
        else:
            return float(value), None

    @classmethod
    def memory_bytes(cls, value: str) -> float:
        base, suffix = cls.split_value(value, 2)
        multipliers = {
            None: 2.0**0,
            'Ki': 2.0**10,
            'Mi': 2.0**20,
            'Gi': 2.0**30,
            'Ti': 2.0**40,
            'Pi': 2.0**50,
            'Ei': 2.0**60
        }
        return base * multipliers[suffix]

    @classmethod
    def cpu_units(cls, value: str) -> float:
        base, suffix = cls.split_value(value, 1)
        multipliers = {
            None: 1e0,
            'n': 1e-9,
            'u': 1e-6,
            # FYI: "precision finer than 1m is not allowed" in cpu limit input
            'm': 1e-3,
            'k': 1e3,
            'M': 1e6,
            'G': 1e9,
            'T': 1e12,
            'P': 1e15,
            'E': 1e18
        }
        return base * multipliers[suffix]

    @classmethod
    async def get_metrics(cls, service_tag_uuid: str, config: Config,
                          logger: Logger):
        cpu_units = []
        memory_bytes = []

        prefix = Kubernetes._get_api_path_prefix('metrics')
        qs = urllib.parse.urlencode({
            'labelSelector': f'service-tag-uuid={service_tag_uuid}'
        })
        res = await Kubernetes.make_k8s_call(config, logger,
                                             f'{prefix}/pods?{qs}')
        Kubernetes.raise_if_not_2xx(res)
        body = json.loads(res.body, encoding='utf-8')
        if len(body['items']) == 0:
            # Metrics not available yet
            return None
        for pod in body['items']:
            # Assert 1:1 container to pod mapping
            if len(pod['containers']) > 1:
                raise K8sError(
                    message=f'Found {len(pod["containers"])} containers '
                    f'in pod {pod["metadata"]["name"]}, expected 1'
                )
            # Convert metrics to standard units (no suffix)
            cpu_units.append(
                cls.cpu_units(pod['containers'][0]['usage']['cpu'])
            )
            memory_bytes.append(
                cls.memory_bytes(pod['containers'][0]['usage']['memory'])
            )

        return {
            'service_tag_uuid': service_tag_uuid,
            'cpu_units': np.percentile(cpu_units, 95),
            'memory_bytes': np.percentile(memory_bytes, 95)
        }

    @classmethod
    async def get_service_tag_uuids(cls, config: Config, apps: list):
        """
        Extracts list of (service_uuid, tag) pairs from apps
        and fetches the uuid for each from the service_tags table
        """
        data = [
            {
                'service_uuid': service[1][ServiceConstants.config]['uuid'],
                'tag': service[1]['tag']
            }
            for app in apps for service in app.services.items()
        ]
        return await Database.get_service_tag_uuids(config, data)

    @classmethod
    async def start_metrics_recorder(cls, config: Config, logger: Logger):
        from .Service import Service
        from .Apps import Apps
        while not Service.shutting_down:
            try:
                apps = list(Apps.apps.values())
                services = await cls.get_service_tag_uuids(config, apps)
                logger.debug(f'Discovered {len(services)} '
                             f'(service_uuid, tag) pairs')
                bulk_update_data = []
                for i in range(0, len(services), cls.BATCH_SIZE):
                    current_batch = services[i: i + cls.BATCH_SIZE]
                    current_data = await asyncio.gather(*[
                        cls.get_metrics(service_tag_uuid, config, logger)
                        for service_tag_uuid in current_batch
                    ])
                    bulk_update_data += current_data
                # Remove all None entries (no corresponding pods found)
                bulk_update_data = [
                    metrics
                    for metrics in bulk_update_data
                    if metrics is not None
                ]
                # Create default records for all new (service_uuid, tag) pairs
                logger.debug(f'Scraped metrics for {len(bulk_update_data)} '
                             f'(service_uuid, tag) pairs')
                await Database.create_service_usage(config, bulk_update_data)
                await Database.update_service_usage(config, bulk_update_data)
                logger.debug(f'Pushed metrics to db, '
                             f'sleeping for {cls.WAIT_PERIOD} seconds')
                # Sleep before updating metrics again
                await asyncio.sleep(cls.WAIT_PERIOD)
            except Exception as e:
                logger.error('Recording resource usage metrics failed', e)
                await asyncio.sleep(5)
