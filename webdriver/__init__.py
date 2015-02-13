# -*- coding: utf-8 -*-

__author__ = 'HAL9000'
__all__ = ['Driver', 'Handler', 'Run', 'bs4', 'request', 'run']

version = "0"
version_info = (0,)

from drivers import Driver, Handler
from libs import bs4, requests

def run():
    from .run import Run
    Run(version=version).run()
