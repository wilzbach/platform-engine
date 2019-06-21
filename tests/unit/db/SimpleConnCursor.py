# -*- coding: utf-8 -*-
from asyncy.db.SimpleConnCursor import SimpleConnCursor

from psycopg2.extras import RealDictCursor


def test_simple(magic):
    conn = magic()
    with SimpleConnCursor(conn) as db:
        assert db.conn == conn
        assert db.cur == conn.cursor(cursor_factory=RealDictCursor)

    conn.cursor().close.assert_called_once()
    conn.close.assert_called_once()
