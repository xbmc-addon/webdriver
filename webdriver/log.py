# -*- coding: utf-8 -*-

__author__ = 'HAL9000'
__all__ = ['make_log', 'set_log', 'get_log']

log = None

def make_log(logfile, nodaemon, debug):
    global log
    import logging
    import logging.handlers
    log = logging.getLogger('webdriver')
    handler = logging.StreamHandler() if nodaemon else logging.handlers.RotatingFileHandler(logfile, maxBytes=10485760, backupCount=100)
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s (%(filename)s:%(lineno)d)'))
    log.setLevel(logging.DEBUG if debug else logging.INFO)
    log.addHandler(handler)

def set_log(logger):
    global log
    log = logger
