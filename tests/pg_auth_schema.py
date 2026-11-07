"""Real-Postgres harness for the auth DB (mock repo; copied from the GUI repo's helper, not imported).

* DSN ``AUTH_TEST_PG_DSN`` (default ``dbname=postgres``); the caller skips only when the
  connection itself fails.
* ONE transaction, rolled back at the end: a throw-away schema is created, ``sql/auth_schema.sql``
  runs inside it, the seed goes in, the code under test runs, then ROLLBACK. Nothing is left.
* ``src.auth.db.connection`` is replaced by a context manager that yields the test connection and
  maps the caller's commit/rollback onto a SAVEPOINT. ``db.cursor``/``fetch_one``/``execute`` look
  ``connection`` up at call time, so they ride the same transaction.
"""

from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from unittest.mock import patch

import psycopg2

DSN = os.environ.get("AUTH_TEST_PG_DSN", "dbname=postgres")
SCHEMA_SQL = (Path(__file__).resolve().parents[1] / "sql" / "auth_schema.sql").read_text()


class PgUnavailable(Exception):
    pass


def one(cur, sql, params=()):
    cur.execute(sql, params)
    return cur.fetchone()[0]


def _seed(cur) -> dict[str, int]:
    """Roles reached every way the usage query counts."""
    ids: dict[str, int] = {}
    for code in ("page:a", "page:b", "page:c"):
        ids[code] = one(cur, "INSERT INTO permissions (code, name) VALUES (%s, %s) RETURNING id", (code, code))
    for key, name, system in (("admin", "Admin", True), ("ops", "Operation Team", True),
                              ("used", "Used Role", False), ("guest", "Guest", True)):
        ids[key] = one(cur, "INSERT INTO roles (name, is_system) VALUES (%s, %s) RETURNING id", (name, system))
    # Operation Team: two matrix rows (copy source). Admin: three (must not be copied).
    cur.execute(
        "INSERT INTO role_permissions (role_id, permission_id, can_view, can_edit, can_export) "
        "VALUES (%s, %s, TRUE, FALSE, FALSE), (%s, %s, TRUE, TRUE, FALSE)",
        (ids["ops"], ids["page:a"], ids["ops"], ids["page:b"]),
    )
    for code in ("page:a", "page:b", "page:c"):
        cur.execute("INSERT INTO role_permissions VALUES (%s, %s, TRUE, TRUE, TRUE)", (ids["admin"], ids[code]))
    # "Used Role": direct holder (also in the team), team-only member, NOC team, one LDAP mapping.
    ids["direct"] = one(cur, "INSERT INTO users (username, display_name) VALUES ('direct', 'Direct') RETURNING id")
    ids["teamonly"] = one(cur, "INSERT INTO users (username, display_name) VALUES ('teamonly', 'Team Only') RETURNING id")
    ids["outsider"] = one(cur, "INSERT INTO users (username) VALUES ('outsider') RETURNING id")
    ids["team"] = one(cur, "INSERT INTO teams (name) VALUES ('NOC') RETURNING id")
    ids["ldap"] = one(
        cur,
        "INSERT INTO ldap_config (name, server_primary, bind_dn, bind_password, search_base_dn) "
        "VALUES ('dc', 'dc1.example', 'cn=svc', 'x', 'dc=example') RETURNING id",
    )
    cur.execute("INSERT INTO user_roles VALUES (%s, %s)", (ids["direct"], ids["used"]))
    cur.execute("INSERT INTO user_roles VALUES (%s, %s)", (ids["outsider"], ids["admin"]))
    cur.execute("INSERT INTO team_members VALUES (%s, %s), (%s, %s)",
                (ids["team"], ids["direct"], ids["team"], ids["teamonly"]))
    cur.execute("INSERT INTO team_roles VALUES (%s, %s)", (ids["team"], ids["used"]))
    ids["mapping"] = one(
        cur,
        "INSERT INTO ldap_group_role_mapping (ldap_config_id, ldap_group_dn, role_id) "
        "VALUES (%s, 'cn=ops,dc=example', %s) RETURNING id",
        (ids["ldap"], ids["used"]),
    )
    return ids


@contextmanager
def auth_pg(schema_prefix: str = "dlp023_mock") -> Iterator[tuple[object, dict[str, int]]]:
    """Yield ``(conn, ids)`` with ``src.auth.db.connection`` bound to a rolled-back transaction."""
    try:
        conn = psycopg2.connect(DSN, connect_timeout=3)
    except psycopg2.OperationalError as exc:
        raise PgUnavailable(str(exc)) from exc
    from src.auth import db as auth_db

    try:
        cur = conn.cursor()
        schema = f"{schema_prefix}_{uuid.uuid4().hex[:12]}"
        cur.execute(f'CREATE SCHEMA "{schema}"')
        cur.execute(f'SET LOCAL search_path TO "{schema}"')
        cur.execute(SCHEMA_SQL)
        ids = _seed(cur)
        cur.close()

        @contextmanager
        def _connection():
            sp = conn.cursor()
            sp.execute("SAVEPOINT caller_tx")
            try:
                yield conn
            except Exception:
                sp.execute("ROLLBACK TO SAVEPOINT caller_tx")
                raise
            else:
                sp.execute("RELEASE SAVEPOINT caller_tx")
            finally:
                sp.close()

        with patch.object(auth_db, "connection", _connection):
            yield conn, ids
    finally:
        conn.rollback()
        conn.close()
