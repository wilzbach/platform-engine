# -*- coding: utf-8 -*-
import json

import asyncpg

from asyncy.Config import Config
from asyncy.entities.ContainerConfig import ContainerConfig
from asyncy.entities.Release import Release
from asyncy.enums.ReleaseState import ReleaseState


import numpy as np

import psycopg2
import psycopg2.extras

_pg_pool = None

class Database:

    @classmethod
    async def pg_pool(cls, config: Config):
        """Create a Connection Pool."""
        global _pg_pool
        if not _pg_pool:
            _pg_pool = await \
                asyncpg.create_pool(dsn=config.POSTGRES,
                                    min_size=5, max_size=15, max_queries=50000,
                                    max_inactive_connection_lifetime=900.0,
                                    init=cls.apply_codecs)
        return _pg_pool

    @classmethod
    async def get_all_app_uuids_for_deployment(cls, config: Config):
        pool = await cls.pg_pool(config)
        # Connection as a context manager is released to the pool on exit
        async with pool.acquire() as con:
            return await con.fetch(
                'select app_uuid uuid from releases group by app_uuid;'
            )

    @classmethod
    async def update_release_state(cls, glogger, config, app_id, version,
                                   state: ReleaseState):
        pool = await cls.pg_pool(config)

        async with pool.acquire() as con:
            # queries in transaction callback are rolled back on failure
            async with con.transaction():

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
        pool = await cls.pg_pool(app.config)

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

        async with pool.acquire() as con:
            data = await con.fetch(query, app.owner_uuid, registry_url)

            result = []
            for config in data:
                result.append(ContainerConfig(name=config['name'],
                                              data=config['containerconfig']))
            return result

    @classmethod
    async def get_release_for_deployment(cls, config, app_id):
        pool = await cls.pg_pool(config)

        query = """
        with latest as (select app_uuid, max(id) as id
                        from releases
                        where state != 'NO_DEPLOY'::release_state
                        group by app_uuid)
        select app_uuid, id as version, config environment,
               payload stories, apps.name as app_name,
               maintenance, always_pull_images,
               hostname app_dns, state, deleted,
               apps.owner_uuid, owner_emails.email as owner_email
        from latest
               inner join releases using (app_uuid, id)
               inner join apps on (latest.app_uuid = apps.uuid)
               inner join app_dns using (app_uuid)
               left join app_public.owner_emails on
                (apps.owner_uuid = owner_emails.owner_uuid)
        where app_uuid = $1;
        """

        async with pool.acquire() as con:
            data = await con.fetchrow(query, app_id)

            return Release(app_uuid=data['app_uuid'],
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
                           owner_email=data['owner_email'])

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

    @classmethod
    def get_all_services(cls, config: Config):
        with cls.new_pg_cur(config) as db:
            query = """
            select owners.username, services.uuid, services.name,
                   services.alias
            from services
            join owners on owner_uuid = owners.uuid;
            """
            db.cur.execute(query)
            return db.cur.fetchall()

    @classmethod
    def create_service_usage(cls, config: Config, data):
        with cls.new_pg_cur(config) as db:
            query = """
            insert into service_usage (service_uuid, tag)
            values %s on conflict (service_uuid, tag) do nothing;
            """
            psycopg2.extras.execute_values(db.cur, query, [
                (s['service_uuid'], s['tag']) for s in data
            ])
            db.conn.commit()

    @classmethod
    def update_service_usage(cls, config: Config, data):

        with cls.new_pg_cur(config) as db:
            query1 = """
            update service_usage
            set cpu_units[next_index] = %(cpu_units)s,
            memory_bytes[next_index] = %(memory_bytes)s
            where service_uuid = %(service_uuid)s and tag = %(tag)s;
            """
            query2 = """
            update service_usage
            set next_index = next_index %% 25 + 1
            where service_uuid = %(service_uuid)s and tag = %(tag)s;
            """
            for record in data:
                db.cur.execute(query1, record)
                db.cur.execute(query2, record)
            db.conn.commit()

    @classmethod
    def get_service_by_alias(cls, config: Config, service_alias: str):
        with cls.new_pg_cur(config) as db:
            query = """
            select uuid from services where alias = %s;
            """
            db.cur.execute(query, (service_alias,))
            return db.cur.fetchone()

    @classmethod
    def get_service_by_slug(cls, config: Config,
                            owner_username: str, service_name: str):
        with cls.new_pg_cur(config) as db:
            query = """
            select services.uuid from services
            join owners on owner_uuid = owners.uuid
            where owners.username = %s and services.name = %s;
            """
            db.cur.execute(query, (owner_username, service_name))
            return db.cur.fetchone()

    @classmethod
    def get_service_limits(cls, config: Config, service: str, tag: str):
        if '/' in service:
            owner_username, service_name = service.split('/')
            service = cls.get_service_by_slug(config,
                                              owner_username, service_name)
        else:
            service = cls.get_service_by_alias(config, service)

        with cls.new_pg_cur(config) as db:
            query = """
            select cpu_units, memory_bytes
            from service_usage
            where service_uuid = %s and tag = %s;
            """
            db.cur.execute(query, (service['uuid'], tag))
            res = db.cur.fetchone()
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
