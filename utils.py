import logging
import logging.config

# Конфигурация логгера
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'default': {
            'format': "%(asctime)s %(levelname)-7s %(name)s [%(filename)s:%(funcName)s:%(lineno)d]\t%(message)s",
            'datefmt': '%Y-%m-%dT%H:%M:%S'
        }
    },

    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': 'pharmacy_simulator.log',
            'mode': 'w',
            'encoding': 'utf-8'
        }
    },

    'loggers': {
        'pharmacy_simulator': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    },

    'root': {
        'level': 'WARNING',
        'handlers': ['console']
    }
}

# Инициализация логгера
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('pharmacy_simulator')
