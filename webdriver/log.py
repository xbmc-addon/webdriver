# -*- coding: utf-8 -*-

__author__ = 'HAL9000'
__all__ = ['log', 'init_log']

import logging
import logging.handlers

log = logging.getLogger('webdriver')

def init_log(logfile, nodaemon, debug):
    handler = logging.StreamHandler() if nodaemon else logging.handlers.RotatingFileHandler(logfile, maxBytes=10485760, backupCount=100)
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s (%(filename)s:%(lineno)d)'))
    log.setLevel(logging.DEBUG if debug else logging.INFO)
    log.addHandler(handler)