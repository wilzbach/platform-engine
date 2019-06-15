from asyncy.Database import Database
from asyncy.enums.ReleaseState import ReleaseState

from pytest import mark


@mark.asyncio
async def test_update_release_state(patch, magic, logger, config):
    conn = magic()
    cur = magic()
    patch.object(Database, 'new_pg_conn', return_value=[conn, cur])
    expected_query = 'update releases ' \
                     'set state = %s ' \
                     'where app_uuid = %s and id = %s;'

    Database.update_release_state(logger, config, 'app_id', 'version',
                                  ReleaseState.DEPLOYED)

    Database.new_pg_conn.assert_called_with(config)
    cur.execute.assert_called_with(
        expected_query, (ReleaseState.DEPLOYED.value, 'app_id', 'version'))

    conn.commit.assert_called()
    cur.close.assert_called()
    conn.close.assert_called()


def test_get_all_app_uuids_for_deployment(patch, magic, config):
    conn = magic()
    cur = magic()
    patch.object(Database, 'new_pg_conn', return_value=(conn, cur))
    query = 'select app_uuid uuid from releases group by app_uuid;'
    ret = Database.get_all_app_uuids_for_deployment(config)
    cur.execute.assert_called_with(query)
    assert ret == cur.fetchall()
