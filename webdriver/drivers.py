# -*- coding: utf-8 -*-

__author__ = 'HAL9000'
__all__ = ['Drivers']

import inspect, os, sys

from .cache import Cache
from .libs import requests


class Handler:
    pass

class Driver:
    def __init__(self, version, cache):
        # TODO: продолжить отсюда
        self.version = version


class Drivers:
    def __init__(self, repo, cache):
        self.cache = Cache(cache)
        self.drivers = {}
        path = os.path.join(repo, 'repo')
        self.repo = os.path.split(path)[0]
        if not os.path.isdir(path):
            os.makedirs(path)
            self.make([])
        self.load()


    def load(self, install=None, uninstall=None):
        for name, obj in self.drivers.items():
            obj['driver'].stop()
            if uninstall and name in uninstall:
                obj['driver'].uninstall()
        self.drivers = {}
        keys = sys.modules.keys()
        for module in keys:
            if module == 'webdriver.repo' or module.startswith('webdriver.repo.'):
                del sys.modules[module]
        sys.path.insert(0, self.repo)
        import repo
        sys.path.pop(0)
        for module in [getattr(repo, x) for x in dir(repo) if not x.startswith('__')]:
            try:
                obj = [x for x in inspect.getmembers(module) if inspect.isclass(x[1]) and issubclass(x[1], Driver) and x[0] != 'Driver'][0][1]()
            except:
                pass



    def make(self, drivers):
        all_list = '__all__=[' + ','.join(['"{0}"'.format(x) for x in drivers]) + ']'
        drivers = ['import {0}'.format(x) for x in drivers]
        drivers.insert(0, all_list)
        drivers.insert(0, '# -*- coding: utf-8 -*-')
        drivers.append('')
        print drivers
        file(os.path.join(self.repo, 'repo', '__init__.py'), 'wb').write('\n'.join(drivers))
