import psycopg2

from .Config import Config
from .enums.ReleaseState import ReleaseState


class Database:

    @classmethod
    def new_pg_conn(cls, config: Config):
        return psycopg2.connect(config.POSTGRES)

    @classmethod
    def get_all_app_uuids_for_deployment(cls, config: Config):
        conn = cls.new_pg_conn(config)
        cur = conn.cursor()

        query = 'select app_uuid from releases group by app_uuid;'
        cur.execute(query)

        return cur.fetchall()

    @classmethod
    def update_release_state(cls, glogger, config, app_id, version,
                             state: ReleaseState):
        conn = cls.new_pg_conn(config)
        cur = conn.cursor()
        query = 'update releases ' \
                'set state = %s ' \
                'where app_uuid = %s and id = %s;'
        cur.execute(query, (state.value, app_id, version))

        conn.commit()
        cur.close()
        conn.close()

        glogger.info(f'Updated state for {app_id}@{version} to {state.name}')

    @classmethod
    def get_docker_configs(cls, app, registry_url):
        conn = cls.new_pg_conn(app.config)
        cur = conn.cursor()
        query = f"""
        with containerconfigs as (select name, owner_uuid, containerconfig,
                                         json_object_keys(
                                             (containerconfig->>'auths')::json
                                         ) registry
                                  from app_public.owner_containerconfigs)
        select name, containerconfig
        from containerconfigs
        where owner_uuid='{app.owner_uuid}' and registry='{registry_url}'
        """
        cur.execute(query)
        all_configs = cur.fetchall()
        return [{'name': c[0], 'dockerconfig': c[1]} for c in all_configs]

    @classmethod
    def get_release_for_deployment(cls, config, app_id):
        conn = cls.new_pg_conn(config)

        curs = conn.cursor()
        query = """
        with latest as (select app_uuid, max(id) as id
                        from releases
                        where state != 'NO_DEPLOY'::release_state
                        group by app_uuid)
        select app_uuid, id, config, payload, maintenance,
               hostname, state, deleted, apps.owner_uuid
        from latest
               inner join releases using (app_uuid, id)
               inner join apps on (latest.app_uuid = apps.uuid)
               inner join app_dns using (app_uuid)
        where app_uuid = %s;
        """
        curs.execute(query, (app_id,))
        release = curs.fetchone()
        return {
            'version': release[1],
            'environment': release[2],
            'stories': release[3],
            'maintenance': release[4],
            'app_dns': release[5],
            'state': release[6],
            'deleted': release[7],
            'owner_uuid': release[8],
        }
