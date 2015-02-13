# -*- coding: utf-8 -*-

__author__ = 'HAL9000'
__all__ = ['Drivers']

import inspect, os, sys

from .cache import Cache

log = None

def get_log():
    from .log import log as logger
    global log
    log = logger



class Handler:
    pass

class Driver:
    def __init__(self, version, did, cache):
        self.version = version
        self.did = did
        self._cache = cache

    def get(self, keys, prefix=None):
        if not prefix:
            prefix = ''
        return self._cache.get(keys, ':'.join([self.did, prefix]))

    def set(self, data, prefix=None):
        if not prefix:
            prefix = ''
        return self._cache.set(data, ':'.join([self.did, prefix]))

    def handle(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def install(self):
        pass

    def uninstall(self):
        pass

    def loop(self):
        pass


class Drivers:
    def __init__(self, version, repo, cache):
        get_log()
        self.version = version
        self.cache = Cache(cache)
        self.drivers = {}
        path = os.path.join(repo, 'repo')
        self.repo = os.path.split(path)[0]
        if not os.path.isdir(path):
            os.makedirs(path)
            self.make([])
        self.load([], [])


    def load(self, install, uninstall):
        self.stop(uninstall)

        sys.path.insert(0, self.repo)
        import repo
        sys.path.pop(0)
        for did, module in [(x, getattr(repo, x)) for x in dir(repo) if not x.startswith('__')]:
            try:
                driver = [x for x in inspect.getmembers(module) if inspect.isclass(x[1]) and issubclass(x[1], Driver) and x[0] != 'Driver'][0][1](self.version, did, self.cache)
            except Exception, e:
                log.warning('driver {0} don`t loaded: {1}'.format(did, str(e)))
            else:
                self.drivers[did] = {'check': 0.0, 'driver': driver}
        self.start(install)
        print self.drivers


    def start(self, install):
        for did, obj in self.drivers.items():
            if did in install:
                obj['driver'].install()
            obj['driver'].start()


    def stop(self, uninstall):
        for did, obj in self.drivers.items():
            obj['driver'].stop()
            if did in uninstall:
                obj['driver'].uninstall()
        self.drivers = {}
        keys = sys.modules.keys()
        for module in keys:
            if module == 'webdriver.repo' or module.startswith('webdriver.repo.'):
                del sys.modules[module]



    def make(self, drivers):
        all_list = '__all__=[' + ','.join(['"{0}"'.format(x) for x in drivers]) + ']'
        drivers = ['import {0}'.format(x) for x in drivers]
        drivers.insert(0, all_list)
        drivers.insert(0, '# -*- coding: utf-8 -*-')
        drivers.append('')
        print drivers
        file(os.path.join(self.repo, 'repo', '__init__.py'), 'wb').write('\n'.join(drivers))

    def check(self):
        for did in self.drivers.keys():
            # TODO: начать отсюда: надо продумать стратегию блокировки тредов (что-то с этим уже бардак полный)
            if self.drivers
