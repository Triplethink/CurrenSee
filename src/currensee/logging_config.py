import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'currensee': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'currensee.extract': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'currensee.transform_load': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'currensee.demo': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


def setup_logging() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)
