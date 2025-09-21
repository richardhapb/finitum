# utils.py
import logging
import sys


def get_logger() -> logging.Logger:
    # Reconfigure stderr/stdout to UTF-8 if possible (py3.7+)
    for stream in (sys.stderr, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    # Build handlers explicitly with UTF-8-safe streams
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    # Force reset any previous basicConfig/handlers
    logging.basicConfig(level=logging.INFO, handlers=[stream_handler], force=True)

    logger = logging.getLogger("fintrack")
    logger.setLevel(logging.INFO)
    return logger
