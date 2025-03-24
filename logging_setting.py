logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '{asctime} - {levelname} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
            'level': 'INFO',
        },
    },
    'loggers': {
        'main': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'start_dialog': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
