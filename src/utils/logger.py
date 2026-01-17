from io import TextIOWrapper
import logging
import sys
from utils.config import DEBUG


def get_logger() -> logging.Logger:
    # Reconfigure stderr/stdout to UTF-8
    for stream in (sys.stderr, sys.stdout):
        try:
            assert isinstance(stream, TextIOWrapper)
            stream.reconfigure(encoding="utf-8")
        except Exception as e:
            print(f"Error configuring logger to utf-8: {e}")

    # Build handlers explicitly with UTF-8-safe streams
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    # Force reset any previous basicConfig/handlers
    logging.basicConfig(level=logging.INFO, handlers=[stream_handler], force=True)

    logger = logging.getLogger("finitum")
    level = logging.DEBUG if DEBUG else logging.INFO
    logger.setLevel(level)
    return logger
