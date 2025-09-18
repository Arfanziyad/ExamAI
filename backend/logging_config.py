LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(asctime)s | %(client_addr)s - "%(request_line)s" %(status_code)s',
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "default",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "server.log",
            "maxBytes": 100000,
            "backupCount": 3,
        },
    },
    "loggers": {
        "": {"handlers": ["default", "file"], "level": "DEBUG"},
        "uvicorn": {"handlers": ["default", "file"], "level": "DEBUG"},
        "uvicorn.error": {"handlers": ["default", "file"], "level": "DEBUG"},
        "uvicorn.access": {"handlers": ["access", "file"], "level": "DEBUG"},
        "sqlalchemy.engine": {"handlers": ["default", "file"], "level": "DEBUG"},
        "fastapi": {"handlers": ["default", "file"], "level": "DEBUG"},
    },
}