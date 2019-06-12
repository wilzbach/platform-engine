import psycopg2

from .Config import Config


class Database:

    @classmethod
    def new_pg_conn(cls, config: Config):
        return psycopg2.connect(config.POSTGRES)
