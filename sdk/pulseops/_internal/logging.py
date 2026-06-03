import logging


def get_sdk_logger() -> logging.Logger:
    logger = logging.getLogger("pulseops.internal")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[pulseops] %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.propagate = False
        logger.setLevel(logging.WARNING)
    return logger