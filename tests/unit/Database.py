from asyncy.Database import Database
from asyncy.enums.ReleaseState import ReleaseState

from pytest import mark


@mark.asyncio
async def test_update_release_state(patch, logger, config):
    patch.object(Database, 'new_pg_conn')
    expected_query = 'update releases ' \
                     'set state = %s ' \
                     'where app_uuid = %s and id = %s;'

    Database.update_release_state(logger, config, 'app_id', 'version',
                                  ReleaseState.DEPLOYED)

    Database.new_pg_conn.assert_called_with(config)
    Database.new_pg_conn.return_value.cursor.assert_called()
    Database.new_pg_conn.return_value.cursor \
        .return_value.execute.assert_called_with(
            expected_query, (ReleaseState.DEPLOYED.value, 'app_id', 'version'))

    Database.new_pg_conn.return_value.commit.assert_called()
    Database.new_pg_conn.return_value.cursor.return_value.close.assert_called()
    Database.new_pg_conn.return_value.close.assert_called()


def test_get_all_app_uuids_for_deployment(patch, magic, config):
    conn = magic()
    patch.object(Database, 'new_pg_conn', return_value=conn)
    query = 'select app_uuid from releases group by app_uuid;'
    ret = Database.get_all_app_uuids_for_deployment(config)
    conn.cursor().execute.assert_called_with(query)
    assert ret == conn.cursor().fetchall()
