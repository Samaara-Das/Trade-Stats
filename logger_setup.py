'''
This is for setting up a logger for the application. Any file can use this to create its own logger.
This was done to avoid repetition of code.
'''

import logging
from logging import getLogger, FileHandler, StreamHandler, Formatter
import sys

def setup_logger(logger_name, logger_level, file='app_log.log'):
    '''This sets up a logger and returns it'''
    logger = getLogger(logger_name)
    logger.setLevel(logger_level)
    
    date_format = "%m.%d.%y %H:%M:%S"
    formatter = Formatter('%(name)s.py %(funcName)s() %(levelname)s: %(message)s %(asctime)s', datefmt=date_format)

    file_handler = FileHandler(file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create a StreamHandler with utf-8 encoding for sys.stdout
    stream_handler = StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
