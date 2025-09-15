from models import *  # noqa: F403
from database import create_db_and_tables


def initialize():
    create_db_and_tables()


if __name__ == "__main__":
    initialize()


