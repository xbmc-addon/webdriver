# -*- coding: utf-8 -*-

__author__ = 'HAL9000'

version = "0"
version_info = (0,)

def run():
    from .run import Run
    Run(version=version).run()
