import os
from models import Expense, Transference  # noqa: F401
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlmodel import SQLModel, Session

load_dotenv()

# ---- Build engines ----------------------------------------------------------


def _ensure_db_utf8(conn_str: str, db_locale: str = "en_US.UTF-8") -> None:
    url = make_url(conn_str)
    dbname = url.database
    if not dbname:
        raise ValueError("CONN_STR must include a database name")

    admin_url = url.set(database="postgres")

    # 1) Check if DB exists + encoding (normal connection; transactions allowed)
    with create_engine(admin_url).connect() as conn:
        exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": dbname}).scalar() is not None
        if exists:
            enc = conn.execute(
                text("SELECT pg_encoding_to_char(encoding) FROM pg_database WHERE datname = :n"),
                {"n": dbname},
            ).scalar_one()
            if enc.upper() == "SQL_ASCII":
                raise RuntimeError(f"Database '{dbname}' exists with SQL_ASCII. DROP it first.")
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


def _build_engine(conn_str: str):
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
    def _force_utf8(dbapi_conn, _):
        # psycopg2: native API exists; psycopg3: fallback to SQL
        try:
            dbapi_conn.set_client_encoding("UTF8")
        except Exception:
            try:
                cur = dbapi_conn.cursor()
                cur.execute("SET client_encoding TO 'UTF8'")
                cur.close()
            except Exception:
                pass

    return engine


# ---- Public API -------------------------------------------------------------

CONN_STR = os.environ.get("CONN_STR", "")
if not CONN_STR:
    raise RuntimeError("Set CONN_STR env var, e.g. postgresql+psycopg://user:pass@localhost/fintrack")

# Ensure DB exists and is UTF-8
_ensure_db_utf8(CONN_STR, db_locale=os.environ.get("DB_LOCALE", "en_US.UTF-8"))

# App engine
engine = _build_engine(CONN_STR)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
