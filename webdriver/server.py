# -*- coding: utf-8 -*-

__author__ = 'HAL9000'
__all__ = ['Server']

import json
import re
import urllib

from .wsgiserver2 import CherryPyWSGIServer, WSGIPathInfoDispatcher

from .drivers import Drivers

class Server:
    def __init__(self, version, host, port, repo, cache, debug=False):
        self.host = host
        self.port = port
        self.drivers = Drivers(version, repo, cache)
        self.debug = debug
        self.reg = re.compile(r'^/([0-9a-f]+)$')

    def start(self):
        # TODO: CherryPy: надо сделать еще обработку error500 и вообще - отлов непойманных ошибок
        handlers = WSGIPathInfoDispatcher({'/execute': self.execute, '/': self.check})
        self.server = CherryPyWSGIServer((self.host, self.port), handlers, server_name='webdriver')
        self.server.start()

    def stop(self):
        self.server.stop()

    def execute(self, environ, response):
        try:
            # TODO: для конвертации полей формы POST-запроса надо воспользоваться модулем CGI
            tasks = json.loads(urllib.unquote((environ['wsgi.input'].read().lstrip('tasks='))))
        except Exception, e:
            return self.error400(response, str(e))
        else:
            if not isinstance(tasks, list):
                return self.error400(response, 'Expect list')

            params = []
            for task in tasks:
                if 'driver' not in task:
                    return self.error400(response, 'Driver not found')

                if 'method' not in task:
                    return self.error400(response, 'Method not found')

                if 'args' in task and not isinstance(task['args'], list):
                    return self.error400(response, 'Unknown args')

                if 'kwargs' in task and not isinstance(task['kwargs'], dict):
                    return self.error400(response, 'Unknown kwargs')

                params.append({'driver': task['driver'], 'method': task['method'], 'args': task.get('args', []), 'kwargs': task.get('kwargs', {})})

            response('200 OK', [('Content-type','text/json')])
            return [json.dumps(params)]

    def check(self, environ, response):
        r = self.reg.search(environ['PATH_INFO'])
        if not r:
            return self.error404(response, '')

        response('200 OK', [('Content-type','text/text')])
        return [r.group(1)]



    def error(self, response, status, msg):
        response(status, [('Content-Type', 'text/plain'), ('Content-Length', str(len(msg)))])
        return [msg]

    def error400(self, response, msg):
        return self.error(response, '400 Bad Request', msg)

    def error404(self, response, msg):
        return self.error(response, '404 Not Found', msg)
