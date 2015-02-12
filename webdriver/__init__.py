# -*- coding: utf-8 -*-

__author__ = 'HAL9000'
__all__ = ['Driver', 'Handler', 'Run']

version = "0"
version_info = (0,)

from drivers import Driver, Handler

def run():
    from .run import Run
    Run(version=version).run()
