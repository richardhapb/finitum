import os
import dotenv
from logging.config import fileConfig

from sqlalchemy import create_engine

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    dotenv.load_dotenv()
    conn_str = os.getenv("CONN_STR")
    if not conn_str:
        raise ConnectionError("CONN_STR doesn't found")

    engine = create_engine(conn_str)

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, version_table_schema="public")

        with context.begin_transaction():
            context.run_migrations()


run_migrations()
