from asyncy.Database import Database
from asyncy.entities.ContainerConfig import ContainerConfig
from asyncy.entities.Release import Release
from asyncy.enums.ReleaseState import ReleaseState


def test_update_release_state(patch, magic, logger, config):
    conn = magic()
    patch.object(Database, 'new_pg_conn', return_value=conn)
    expected_query = 'update releases ' \
                     'set state = %s ' \
                     'where app_uuid = %s and id = %s;'

    Database.update_release_state(logger, config, 'app_id', 'version',
                                  ReleaseState.DEPLOYED)

    Database.new_pg_conn.assert_called_with(config)
    conn.cursor().execute.assert_called_with(
        expected_query, (ReleaseState.DEPLOYED.value, 'app_id', 'version'))

    conn.commit.assert_called()
    conn.cursor().close.assert_called()
    conn.close.assert_called()


def test_get_all_app_uuids_for_deployment(patch, magic, config):
    conn = magic()
    patch.object(Database, 'new_pg_conn', return_value=conn)
    query = 'select app_uuid uuid from releases group by app_uuid;'
    ret = Database.get_all_app_uuids_for_deployment(config)
    conn.cursor().execute.assert_called_with(query)
    assert ret == conn.cursor().fetchall()

    conn.cursor().close.assert_called()
    conn.close.assert_called()


def test_get_container_configs(patch, magic, config):
    conn = magic()
    patch.object(Database, 'new_pg_conn', return_value=conn)
    expected_query = """
            with containerconfigs as (select name, owner_uuid, containerconfig,
                                             json_object_keys(
                                                 (containerconfig->>'auths')::json
                                             ) registry
                                      from app_public.owner_containerconfigs)
            select name, containerconfig
            from containerconfigs
            where owner_uuid = %s and registry = %s
            """

    patch.object(conn.cursor(), 'fetchall', return_value=[
        {'name': 'n1', 'containerconfig': 'config'}
    ])
    app = magic()
    app.config = config
    app.owner_uuid = 'my_owner_uuid'
    registry_url = 'my_registry_url_here'
    ret = Database.get_container_configs(app, registry_url)

    assert ret == [
        ContainerConfig(name='n1', data='config')
    ]

    conn.cursor().execute.assert_called_with(expected_query,
                                             (app.owner_uuid, registry_url))

    conn.cursor().close.assert_called()
    conn.close.assert_called()


def test_get_release_for_deployment(patch, magic, config):
    app_id = 'my_app_id'
    conn = magic()
    patch.object(Database, 'new_pg_conn', return_value=conn)
    expected_query = """
            with latest as (select app_uuid, max(id) as id
                            from releases
                            where state != 'NO_DEPLOY'::release_state
                            group by app_uuid)
            select app_uuid, id as version, config environment,
                   payload stories,
                   maintenance, hostname app_dns, state, deleted,
                   apps.owner_uuid
            from latest
                   inner join releases using (app_uuid, id)
                   inner join apps on (latest.app_uuid = apps.uuid)
                   inner join app_dns using (app_uuid)
            where app_uuid = %s;
            """

    patch.object(conn.cursor(), 'fetchone', return_value={
        'app_uuid': 'my_app_uuid',
        'version': 'my_version',
        'environment': 'my_environment',
        'stories': 'my_stories',
        'maintenance': 'my_maintenance',
        'app_dns': 'my_app_dns',
        'state': 'my_state',
        'deleted': 'my_deleted',
        'owner_uuid': 'my_owner_uuid',
    })

    ret = Database.get_release_for_deployment(config, app_id)

    assert ret == Release(
        app_uuid='my_app_uuid',
        version='my_version',
        environment='my_environment',
        stories='my_stories',
        maintenance='my_maintenance',
        app_dns='my_app_dns',
        state='my_state',
        deleted='my_deleted',
        owner_uuid='my_owner_uuid',
    )

    conn.cursor().execute.assert_called_with(expected_query, (app_id,))

    conn.cursor().close.assert_called()
    conn.close.assert_called()
