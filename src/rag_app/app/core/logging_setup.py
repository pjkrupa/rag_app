import logging
from logging.handlers import RotatingFileHandler

def get_logger(
        name=__name__, 
        path='rag.log', 
        console_level=logging.WARNING,
        file_level=logging.DEBUG
        ):
    logger = logging.getLogger(name=name)
    logger.setLevel(logging.DEBUG)

    file_handler = RotatingFileHandler(
        path, 
        maxBytes=5_000_000,   # 5 MB
        backupCount=3,
        encoding="utf-8"
    )

    console_handler = logging.StreamHandler()

    file_handler.setLevel(file_level)
    console_handler.setLevel(console_level)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    formatter = logging.Formatter( 
        "{asctime} | {levelname:<8} | {module}.{funcName}:{lineno} | {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    return logger