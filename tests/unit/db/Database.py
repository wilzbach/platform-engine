# -*- coding: utf-8 -*-

from asyncy.db.Database import Database
from asyncy.entities.ContainerConfig import ContainerConfig
from asyncy.entities.Release import Release
from asyncy.enums.ReleaseState import ReleaseState

import numpy as np

from pytest import fixture, mark



@fixture
def database(magic, patch, async_cm_mock, async_mock):
    conn = magic()
    conn.transaction.return_value = async_cm_mock()
    conn.execute = async_mock()
    # conn.execute = async_mock(return_value=lambda **args: args)
    patch.object(Database, 'pg_conn', new=async_mock(return_value=conn))
    return conn


@mark.asyncio
async def test_update_release_state(logger, config, database):
    expected_query = '''\
                update releases 
                set state = $1
                where app_uuid = $2 and id = $3;
            '''

    await Database.update_release_state(logger, config, 'app_id', 'version',
                                        ReleaseState.DEPLOYED)

    Database.pg_conn.mock.assert_called_with(config)
    database.execute.mock.assert_called_with(
        expected_query, ReleaseState.DEPLOYED.value, 'app_id', 'version')


@mark.asyncio
async def test_get_all_app_uuids_for_deployment(magic, config, database, async_mock):
    stmt = magic()
    stmt.fetch = async_mock()
    database.prepare = async_mock(return_value=stmt)

    await Database.get_all_app_uuids_for_deployment(config)
    database.prepare.mock.assert_called_with(query)
    stmt.fetch.mock.assert_called_once()

@mark.asyncio
async def test_get_release_for_deployment(patch, config, database, async_mock):
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
               apps.owner_uuid, owner_emails.email as owner_email
        from latest
               inner join releases using (app_uuid, id)
               inner join apps on (latest.app_uuid = apps.uuid)
               inner join app_dns using (app_uuid)
               left join app_public.owner_emails on
                (apps.owner_uuid = owner_emails.owner_uuid)
        where app_uuid = $1;
        """

    patch.object(database, 'fetchrow', new=async_mock(
        return_value={
            'app_uuid': 'my_app_uuid',
            'app_name': 'my_app_name',
            'version': 'my_version',
            'environment': 'my_environment',
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
        owner_email='my_owner_email'
    )

    database.fetchrow.mock.assert_called_with(expected_query, app_id)


def test_get_all_services(config, database):

    query = """
            select owners.username, services.uuid, services.name,
                   services.alias
            from services
            join owners on owner_uuid = owners.uuid;
            """
    ret = Database.get_all_services(config)
    database.cur.execute.assert_called_with(query)
    assert ret == database.cur.fetchall()


def test_create_service_usage(patch, config, database):
    data = [{
        'service_uuid': '2614fee0-6b2a-4cd8-b4e6-6bbeab4eff84',
        'tag': 'v1'
    }, {
        'service_uuid': 'e1660927-bbad-4936-a005-ee2b1ab9eb0b',
        'tag': 'latest'
    }]
    query = """
            insert into service_usage (service_uuid, tag)
            values %s on conflict (service_uuid, tag) do nothing;
            """
    patch.object(psycopg2.extras, 'execute_values')
    Database.create_service_usage(config, data)
    psycopg2.extras.execute_values.assert_called_with(database.cur, query, [
        (s['service_uuid'], s['tag']) for s in data
    ])
    database.conn.commit.assert_called()


def test_update_service_usage(config, database):
    data = [{
        'service_uuid': '2614fee0-6b2a-4cd8-b4e6-6bbeab4eff84',
        'tag': 'v1'
    }, {
        'service_uuid': 'e1660927-bbad-4936-a005-ee2b1ab9eb0b',
        'tag': 'latest'
    }]
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
    Database.update_service_usage(config, data)
    assert database.cur.execute.mock_calls == [
        mock.call(query, record)
        for record in data for query in [query1, query2]
    ]
    database.conn.commit.assert_called()


def test_get_service_by_alias(config, database):
    alias = 'slack'
    query = """
            select uuid from services where alias = %s;
            """
    ret = Database.get_service_by_alias(config, alias)
    database.cur.execute.assert_called_with(query, (alias,))
    assert ret == database.cur.fetchone()


def test_get_service_by_slug(config, database):
    owner_username = 'microservices'
    service_name = 'slack'
    query = """
            select services.uuid from services
            join owners on owner_uuid = owners.uuid
            where owners.username = %s and services.name = %s;
            """
    ret = Database.get_service_by_slug(config, owner_username, service_name)
    database.cur.execute.assert_called_with(query,
                                            (owner_username, service_name))
    assert ret == database.cur.fetchone()


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
def test_get_service_limits(patch, config, database, service, limits):
    query = """
            select cpu_units, memory_bytes
            from service_usage
            where service_uuid = %s and tag = %s;
            """
    service_uuid = 'e1660927-bbad-4936-a005-ee2b1ab9eb0b'
    tag = 'latest'
    patch.object(Database, 'get_service_by_slug',
                 return_value={'uuid': service_uuid})
    patch.object(Database, 'get_service_by_alias',
                 return_value={'uuid': service_uuid})
    patch.object(database.cur, 'fetchone', return_value=limits)
    ret = Database.get_service_limits(config, service, tag)
    if '/' in service:
        Database.get_service_by_slug.assert_called_with(config,
                                                        *service.split('/'))
    else:
        Database.get_service_by_alias.assert_called_with(config, service)
    database.cur.execute.assert_called_with(query, (service_uuid, tag))
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
