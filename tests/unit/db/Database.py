# -*- coding: utf-8 -*-
import asyncpg

from asyncy.db.Database import Database
from asyncy.entities.ContainerConfig import ContainerConfig
from asyncy.entities.Release import Release
from asyncy.enums.AppEnvironment import AppEnvironment
from asyncy.enums.ReleaseState import ReleaseState

import numpy as np

from pytest import fixture, mark


@fixture
def pool(magic, patch, async_cm_mock, async_mock):
    con = magic()

    patch.object(con, 'execute_many',
                 new=async_mock(side_effect=lambda query, *args:
                                (query, *args)))

    con.fetchrow = async_mock(side_effect=lambda query, *args: (query, *args))
    con.fetch = async_mock(side_effect=lambda query, *args: (query, *args))
    con.execute = async_mock(side_effect=lambda query, *args: (query, *args))
    con.execute_many = async_mock(side_effect=lambda query, *args:
                                  (query, *args))

    con.transaction.return_value = async_cm_mock()
    con.transaction.return_value.aenter = con

    pool = magic()
    pool.acquire.return_value = async_cm_mock()
    patch.object(Database, 'get_pooled_conn', return_value=async_cm_mock())

    pool.con = con

    patch.object(Database, 'pg_pool', new=async_mock(return_value=pool))

    return pool


@mark.asyncio
async def test_database_connect(patch, magic, config,
                                async_mock, async_cm_mock):
    patch.object(asyncpg, 'create_pool', new=async_mock())
    pool = await Database.pg_pool(config)
    asyncpg.create_pool.mock.assert_called_once()

    patch.object(asyncpg, 'connect', new=async_mock())
    await Database.new_con(config)
    asyncpg.connect.mock.assert_called_once()

    patch.object(asyncpg, 'connect', new=async_mock())
    await Database.new_con(config)
    asyncpg.connect.mock.assert_called_once()

    pool.acquire.return_value = async_cm_mock()
    pool.acquire.return_value.aenter = 'test-con'
    patch.object(asyncpg, 'connect', new=async_mock())
    async with Database.get_pooled_conn(config) as res:
        assert res == 'test-con'
        assert pool.acquire.call_count == 1


@mark.asyncio
async def test_update_release_state(logger, config, pool):
    expected_query = """\
                update releases
                set state = $1
                where app_uuid = $2 and id = $3;
            """

    await Database.update_release_state(logger, config, 'app_id', 'version',
                                        ReleaseState.DEPLOYED)

    assert Database.get_pooled_conn.call_count == 1
    pool.con.execute.mock.assert_called_with(
        expected_query, ReleaseState.DEPLOYED.value, 'app_id', 'version')


@mark.asyncio
async def test_get_all_app_uuids_for_deployment(config, pool):
    query = """
            select app_uuid uuid
            from releases
                     inner join apps on releases.app_uuid = apps.uuid
            where environment = %1
            group by app_uuid;
            """
    await Database.get_all_app_uuids_for_deployment(config)
    assert Database.get_pooled_conn.call_count == 1
    pool.con.fetch.mock.assert_called_with(query, config.APP_ENVIRONMENT.value)


@mark.asyncio
async def test_get_container_configs(patch, magic, config,
                                     pool, async_mock):
    patch.object(pool.con, 'fetch', new=async_mock(return_value=[
        {'name': 'n1', 'containerconfig': 'config'}
    ]))

    expected_query = """
                with containerconfigs as
                (select name, owner_uuid,
                    containerconfig, json_object_keys
                    ((containerconfig->>'auths')::json) registry
                from app_public.owner_containerconfigs)
                select name, containerconfig
                from containerconfigs
                where owner_uuid = $1 and registry = $2
            """

    app = magic()
    app.config = config
    app.owner_uuid = 'my_owner_uuid'
    registry_url = 'my_registry_url_here'
    ret = await Database.get_container_configs(app, registry_url)

    assert Database.get_pooled_conn.call_count == 1

    assert ret == [
        ContainerConfig(name='n1', data='config')
    ]

    pool.con.fetch.mock \
        .assert_called_with(expected_query, app.owner_uuid,
                            registry_url)


@mark.asyncio
@mark.parametrize('app_environment', ['PRODUCTION', 'STAGING', 'DEV'])
async def test_get_release_for_deployment(patch, config, pool, async_mock, app_environment):
    app_id = 'my_app_id'
    expected_query = """
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

    patch.object(pool.con, 'fetchrow',
                 new=async_mock(return_value={
                     'app_uuid': 'my_app_uuid',
                     'app_name': 'my_app_name',
                     'version': 'my_version',
                     'environment': 'my_environment',
                     'app_environment': app_environment,
                     'stories': 'my_stories',
                     'maintenance': 'my_maintenance',
                     'always_pull_images': 'my_always_pull_images',
                     'app_dns': 'my_app_dns',
                     'state': 'my_state',
                     'deleted': 'my_deleted',
                     'owner_uuid': 'my_owner_uuid',
                     'owner_email': 'my_owner_email'
                 })
                 )
    ret = await Database.get_release_for_deployment(config, app_id)

    assert Database.get_pooled_conn.call_count == 1
    assert ret == Release(
        app_uuid='my_app_uuid',
        app_name='my_app_name',
        version='my_version',
        environment='my_environment',
        stories='my_stories',
        maintenance='my_maintenance',
        always_pull_images='my_always_pull_images',
        app_dns='my_app_dns',
        state='my_state',
        deleted='my_deleted',
        owner_uuid='my_owner_uuid',
        owner_email='my_owner_email',
        app_environment=AppEnvironment[app_environment]
    )

    pool.con.fetchrow.mock.assert_called_with(expected_query, app_id)


@mark.asyncio
async def test_get_all_services(config, pool):
    query = """
            select owners.username, services.uuid, services.name,
                   services.alias
            from services
            join owners on owner_uuid = owners.uuid;
            """
    ret = await Database.get_all_services(config)
    assert Database.get_pooled_conn.call_count == 1
    pool.con.fetch.mock.assert_called_with(query)
    assert ret == await pool.con.fetch(query)


@mark.asyncio
async def test_create_service_usage(patch, config, pool, async_mock):
    patch.object(Database, 'pg_pool', new=async_mock(return_value=pool))
    data = [{
        'service_uuid': '2614fee0-6b2a-4cd8-b4e6-6bbeab4eff84',
        'tag': 'v1'
    }, {
        'service_uuid': 'e1660927-bbad-4936-a005-ee2b1ab9eb0b',
        'tag': 'latest'
    }]

    query = """
                insert into service_usage (service_uuid, tag)
                values ($1, $2) on conflict (service_uuid, tag) do nothing;
                """

    await Database.create_service_usage(config, data)
    assert Database.get_pooled_conn.call_count == 1
    assert pool.con.transaction.call_count == 1
    pool.con.execute_many.mock.assert_called_once()
    pool.con.execute_many.mock.assert_called_with(query, [
        (s['service_uuid'], s['tag']) for s in data
    ])


@mark.asyncio
async def test_update_service_usage(config, pool):
    data = [{
        'cpu_units': 2,
        'memory_bytes': 100,
        'service_uuid': '2614fee0-6b2a-4cd8-b4e6-6bbeab4eff84',
        'tag': 'v1'
    }, {
        'cpu_units': 1,
        'memory_bytes': 50,
        'service_uuid': 'e1660927-bbad-4936-a005-ee2b1ab9eb0b',
        'tag': 'latest'
    }]
    query1 = """
            update service_usage
            set cpu_units[next_index] = $1,
            memory_bytes[next_index] = $2
            where service_uuid = $3 and tag = $4;
            """
    query2 = """
            update service_usage
            set next_index = next_index %% 25 + 1
            where service_uuid = $1 and tag = $2;
            """
    await Database.update_service_usage(config, data)

    pool.con.execute_many.mock \
        .assert_any_call(query1,
                         [(2, 100, '2614fee0-6b2a-4cd8-b4e6-6bbeab4eff84',
                           'v1'),
                          (1, 50, 'e1660927-bbad-4936-a005-ee2b1ab9eb0b',
                           'latest')])
    pool.con.execute_many.mock \
        .assert_any_call(query2,
                         [('2614fee0-6b2a-4cd8-b4e6-6bbeab4eff84', 'v1'),
                          ('e1660927-bbad-4936-a005-ee2b1ab9eb0b', 'latest')])


@mark.asyncio
async def test_get_service_by_alias(config, pool):
    alias = 'slack'
    query = """
            select uuid from services where alias = $1;
            """
    ret = await Database.get_service_by_alias(config, alias)
    pool.con.fetchrow.mock.assert_called_with(query, alias, )
    assert Database.get_pooled_conn.call_count == 1
    assert ret == await pool.con.fetchrow(query, alias)


@mark.asyncio
async def test_get_service_by_slug(config, pool):
    owner_username = 'microservices'
    service_name = 'slack'
    query = """
            select services.uuid from services
            join owners on owner_uuid = owners.uuid
            where owners.username = $1 and services.name = $2;
            """
    ret = await Database. \
        get_service_by_slug(config, owner_username, service_name)
    pool.con.fetchrow.mock \
        .assert_called_with(query, owner_username, service_name)
    assert ret == await pool.con.fetchrow(query, owner_username, service_name)
    assert Database.get_pooled_conn.call_count == 1


@mark.parametrize('service', [
    'slack',
    'microservices/slack'
])
@mark.parametrize('limits', [{
    'memory_bytes': [-1],
    'cpu_units': [-1]
}, {
    'memory_bytes': [1, 2, 3, 4],
    'cpu_units': [5, 6, 7, 8]
}, {
    'memory_bytes': [209715000] * 10,
    'cpu_units': [0] * 10
}, None
])
@mark.asyncio
async def test_get_service_limits(patch, config, pool,
                                  service, limits, async_mock):
    query = """
            select cpu_units, memory_bytes
            from service_usage
            where service_uuid = $1 and tag = $2;
            """
    service_uuid = 'e1660927-bbad-4936-a005-ee2b1ab9eb0b'
    tag = 'latest'
    patch.object(Database, 'get_service_by_slug',
                 new=async_mock(return_value={'uuid': service_uuid}))
    patch.object(Database, 'get_service_by_alias',
                 new=async_mock(return_value={'uuid': service_uuid}))
    patch.object(pool.con, 'fetchrow',
                 new=async_mock(return_value=limits))
    ret = await Database.get_service_limits(config, service, tag)
    assert Database.get_pooled_conn.call_count == 1
    if '/' in service:
        Database.get_service_by_slug.mock \
            .assert_called_with(config, *service.split('/'))
    else:
        Database.get_service_by_alias.mock.assert_called_with(config, service)
    pool.con.fetchrow.mock.assert_called_with(query, service_uuid, tag)
    if limits is None or -1 in limits['memory_bytes']:
        assert ret == {
            'cpu': 0,
            'memory': 209715000  # 200Mi
        }
    else:
        assert ret == {
            'cpu': 1.25 * np.percentile(limits['cpu_units'], 95),
            'memory': min(
                209715000,
                1.25 * np.percentile(limits['memory_bytes'], 95)
            )
        }
