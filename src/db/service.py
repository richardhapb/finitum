import os
from collections.abc import Generator

from sqlalchemy import create_engine, event, text, Engine
from sqlalchemy.engine import make_url
from sqlmodel import Session

from utils.logger import get_logger

logger = get_logger()


def _ensure_db_utf8(conn_str: str, db_locale: str = "en_US.UTF-8") -> None:
    url = make_url(conn_str)
    dbname = url.database
    if not dbname:
        raise ValueError("CONN_STR must include a database name")

    admin_url = url.set(database="postgres")

    # Check if DB exists + encoding (normal connection; transactions allowed)
    with create_engine(admin_url).connect() as conn:
        exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": dbname}).scalar() is not None
        if exists:
            enc = conn.execute(
                text("SELECT pg_encoding_to_char(encoding) FROM pg_database WHERE datname = :n"),
                {"n": dbname},
            ).scalar_one()
            if enc.upper() == "SQL_ASCII":
                raise RuntimeError("Database '%s' exists with SQL_ASCII. DROP it first.", dbname)
            return  # already OK

    if "'" in db_locale:
        raise ValueError("DB_LOCALE must not contain single quotes")

    create_sql = (
        f"CREATE DATABASE {dbname} "
        "WITH TEMPLATE template0 ENCODING 'UTF8' "
        f"LC_COLLATE '{db_locale}' LC_CTYPE '{db_locale}'"
    )

    with create_engine(admin_url, isolation_level="AUTOCOMMIT").connect() as conn:
        conn.exec_driver_sql(create_sql)


def _build_engine(conn_str: str) -> Engine:
    """
    Build the app engine and force client_encoding UTF8 on connect
    (works with psycopg2 and psycopg3).
    """
    engine = create_engine(
        conn_str,
        pool_pre_ping=True,
        # psycopg3 obeys options; psycopg2 ignores it but we also set via event below.
        connect_args={"options": "-c client_encoding=UTF8"},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _force_utf8(dbapi_conn, _) -> None:  # noqa: ANN001
        # psycopg2: native API exists; psycopg3: fallback to SQL
        try:
            dbapi_conn.set_client_encoding("UTF8")
        except Exception:
            try:
                cur = dbapi_conn.cursor()
                cur.execute("SET client_encoding TO 'UTF8'")
                cur.close()
            except Exception as e:
                logger.error("Error setting database to UTF8: %s", e)

    return engine


engine: Engine | None = None


def get_engine() -> Engine:
    global engine  # noqa: PLW0603
    if engine:
        return engine

    conn_str = os.environ.get("CONN_STR")
    if not conn_str:
        raise RuntimeError("Set CONN_STR env var, e.g. postgresql+psycopg://user:pass@localhost/finitum")

    # Ensure DB exists and is UTF-8
    _ensure_db_utf8(conn_str, db_locale=os.environ.get("DB_LOCALE", "en_US.UTF-8"))

    # App engine
    engine = _build_engine(conn_str)
    return engine


def get_session() -> Generator[Session]:
    engine = get_engine()
    with Session(engine) as session:
        yield session
