# -*- coding: utf-8 -*-
import json
from contextlib import asynccontextmanager

import asyncpg

from asyncy.Config import Config
from asyncy.entities.ContainerConfig import ContainerConfig
from asyncy.entities.Release import Release
from asyncy.enums.AppEnvironment import AppEnvironment
from asyncy.enums.ReleaseState import ReleaseState

import numpy as np

_pg_pool = None


class Database:

    @classmethod
    async def pg_pool(cls, config: Config):
        """Create a Connection Pool."""
        global _pg_pool
        if not _pg_pool:
            _pg_pool = await \
                asyncpg.create_pool(dsn=config.POSTGRES_URI,
                                    min_size=5, max_size=15, max_queries=50000,
                                    max_inactive_connection_lifetime=900.0,
                                    init=cls.apply_codecs)
        return _pg_pool

    @classmethod
    @asynccontextmanager
    async def get_pooled_conn(cls, config: Config):
        pool = await cls.pg_pool(config)
        async with pool.acquire() as conn:
            yield conn

    @classmethod
    async def new_con(cls, config: Config):
        return await asyncpg.connect(dsn=config.POSTGRES_URI)

    @classmethod
    async def get_all_app_uuids_for_deployment(cls, config: Config):
        # Connection within a context manager is released to the pool on exit
        async with cls.get_pooled_conn(config) as con:
            query = """
            select app_uuid uuid
            from releases
                     inner join apps on releases.app_uuid = apps.uuid
            where environment = $1
            group by app_uuid;
            """
            return await con.fetch(query, config.APP_ENVIRONMENT.value)

    @classmethod
    async def update_release_state(cls, glogger, config, app_id, version,
                                   state: ReleaseState):
        async with cls.get_pooled_conn(config) as con:
            result = await con.execute("""\
                update releases
                set state = $1
                where app_uuid = $2 and id = $3;
            """, state.value, app_id, version)

            glogger.info(f'Updated state for {app_id}@{version}'
                         f' to {state.name}')

            return result

    @classmethod
    async def get_container_configs(cls, app, registry_url):
        query = """
                with containerconfigs as
                (select name, owner_uuid,
                    containerconfig, json_object_keys
                    ((containerconfig->>'auths')::json) registry
                from app_public.owner_containerconfigs)
                select name, containerconfig
                from containerconfigs
                where owner_uuid = $1 and registry = $2
            """

        async with cls.get_pooled_conn(app.config) as con:
            data = await con.fetch(query, app.owner_uuid, registry_url)

            result = []
            for config in data:
                result.append(ContainerConfig(name=config['name'],
                                              data=config['containerconfig']))
            return result

    @classmethod
    async def get_release_for_deployment(cls, config, app_id):
        query = """
        with latest as (select app_uuid, max(id) as id
                        from releases
                        where state != 'NO_DEPLOY'::release_state
                        group by app_uuid)
        select app_uuid, id as version, config environment,
               payload stories, apps.name as app_name,
               maintenance, always_pull_images,
               hostname app_dns, state, deleted,
               apps.owner_uuid, owner_emails.email as owner_email,
               environment app_environment
        from latest
               inner join releases using (app_uuid, id)
               inner join apps on (latest.app_uuid = apps.uuid)
               inner join app_dns using (app_uuid)
               left join app_public.owner_emails on
                (apps.owner_uuid = owner_emails.owner_uuid)
        where app_uuid = $1;
        """
        async with cls.get_pooled_conn(config) as con:
            data = await con.fetchrow(query, app_id)

        return Release(
            app_uuid=data['app_uuid'],
            app_environment=AppEnvironment[data['app_environment']],
            app_name=data['app_name'],
            version=data['version'],
            environment=data['environment'],
            stories=data['stories'],
            maintenance=data['maintenance'],
            always_pull_images=data['always_pull_images'],
            app_dns=data['app_dns'],
            state=data['state'],
            deleted=data['deleted'],
            owner_uuid=data['owner_uuid'],
            owner_email=data['owner_email']
        )

    @classmethod
    async def get_service_tag_uuids(cls, config: Config, data: list) -> list:
        async with cls.get_pooled_conn(config) as con:
            query = """
            select distinct uuid
            from service_tags
            where service_uuid = $1 and tag = $2;
            """
            stmt = await con.prepare(query)
            res = [
                await stmt.fetchrow(d['service_uuid'], d['tag']) for d in data
            ]
            return [row['uuid'] for row in res]

    @classmethod
    async def create_service_usage(cls, config: Config, data):
        async with cls.get_pooled_conn(config) as con:
            # queries in transaction callback are rolled back on failure
            async with con.transaction():
                query = """
                insert into service_usage (service_tag_uuid)
                values ($1) on conflict (service_tag_uuid) do nothing;
                """
                await con.executemany(query, [
                    (d['service_tag_uuid'],) for d in data
                ])

    @classmethod
    async def update_service_usage(cls, config: Config, data):
        async with cls.get_pooled_conn(config) as con:
            update_service_resources_stmt = """
            update service_usage
            set cpu_units[next_index] = $1, memory_bytes[next_index] = $2
            where service_tag_uuid = $3;
            """
            update_next_index_stmt = """
            update service_usage
            set next_index = next_index % 25 + 1
            where service_tag_uuid = $1;
            """

            await con.executemany(update_service_resources_stmt, [
                (record['cpu_units'], record['memory_bytes'],
                 record['service_tag_uuid'])
                for record in data
            ])

            await con.executemany(update_next_index_stmt, [
                (record['service_tag_uuid'],)
                for record in data
            ])

    @classmethod
    async def get_service_limits(cls, config: Config, service_tag_uuid: str):
        async with cls.get_pooled_conn(config) as con:
            query = """
            select cpu_units, memory_bytes
            from service_usage
            where service_tag_uuid = $1;
            """
            res = await con.fetchrow(query, service_tag_uuid)
            if res is None or -1 in res['memory_bytes']:
                limits = {
                    'cpu': 0,
                    'memory': 209715000  # 200Mi
                }
            else:
                limits = {
                    'cpu': 1.25 * np.percentile(res['cpu_units'], 95),
                    'memory': min(
                        209715000,  # 200Mi
                        1.25 * np.percentile(res['memory_bytes'], 95)
                    )
                }
            return limits

    @staticmethod
    async def apply_codecs(con):
        await con.set_type_codec(
            'json',
            encoder=json.dumps,
            decoder=json.loads,
            schema='pg_catalog'
        )
        await con.set_type_codec(
            'jsonb',
            encoder=json.dumps,
            decoder=json.loads,
            schema='pg_catalog',
        )
        await con.set_type_codec(
            'uuid',
            encoder=str,
            decoder=str,
            schema='pg_catalog',
        )
