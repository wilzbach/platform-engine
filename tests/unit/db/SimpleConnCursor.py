# -*- coding: utf-8 -*-
from asyncy.db.SimpleConnCursor import SimpleConnCursor

from psycopg2.extras import RealDictCursor


def test_simple(magic):
    conn = magic()
    with SimpleConnCursor(conn) as db:
        assert db.conn == conn
        conn.cursor.assert_called_with(cursor_factory=RealDictCursor)

    conn.cursor().close.assert_called_once()
    conn.close.assert_called_once()
