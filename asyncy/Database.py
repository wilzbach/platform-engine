import psycopg2
from psycopg2.extras import RealDictCursor

from .Config import Config
from .entities.ContainerConfig import ContainerConfig
from .entities.Release import Release
from .enums.ReleaseState import ReleaseState


class Database:

    @classmethod
    def new_pg_conn(cls, config: Config):
        conn = psycopg2.connect(config.POSTGRES)
        return conn

    @classmethod
    def get_all_app_uuids_for_deployment(cls, config: Config):
        conn = cls.new_pg_conn(config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            query = 'select app_uuid uuid from releases group by app_uuid;'
            cur.execute(query)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @classmethod
    def update_release_state(cls, glogger, config, app_id, version,
                             state: ReleaseState):
        conn = cls.new_pg_conn(config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            query = 'update releases ' \
                    'set state = %s ' \
                    'where app_uuid = %s and id = %s;'
            cur.execute(query, (state.value, app_id, version))
            conn.commit()
        finally:
            cur.close()
            conn.close()

        glogger.info(f'Updated state for {app_id}@{version} to {state.name}')

    @classmethod
    def get_container_configs(cls, app, registry_url):
        conn = cls.new_pg_conn(app.config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            query = """
            with containerconfigs as (select name, owner_uuid, containerconfig,
                                             json_object_keys(
                                                 (containerconfig->>'auths')::json
                                             ) registry
                                      from app_public.owner_containerconfigs)
            select name, containerconfig
            from containerconfigs
            where owner_uuid = %s and registry = %s
            """
            cur.execute(query, (app.owner_uuid, registry_url))
            data = cur.fetchall()
            result = []
            for config in data:
                result.append(ContainerConfig(name=config['name'],
                                              data=config['containerconfig']))
            return result
        finally:
            cur.close()
            conn.close()

    @classmethod
    def get_release_for_deployment(cls, config, app_id):
        conn = cls.new_pg_conn(config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            query = """
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
            cur.execute(query, (app_id,))
            data = cur.fetchone()
            return Release(app_uuid=data['app_uuid'], version=data['version'],
                           environment=data['environment'],
                           stories=data['stories'],
                           maintenance=data['maintenance'],
                           app_dns=data['app_dns'],
                           state=data['state'], deleted=data['deleted'],
                           owner_uuid=data['owner_uuid'])
        finally:
            cur.close()
            conn.close()
