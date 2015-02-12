# -*- coding: utf-8 -*-

__author__ = 'HAL9000'
__all__ = ['Server']

import atexit
import json
import os
import re
import sys
import signal
import subprocess
import time
import urllib

from .log import log
from .wsgiserver2 import CherryPyWSGIServer, WSGIPathInfoDispatcher

from .drivers import Drivers

class Server:
    def __init__(self, version, host, port, repo, cache, debug=False):
        self.version = version
        self.host = host
        self.port = port
        self.drivers = Drivers(repo, cache)
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



class Server2:
    def __init__(self, host='0.0.0.0', port=2020, pidfile=None, logfile=None, cache=None, nodaemon=False, debug=False):
        self.host = host or '0.0.0.0'
        self.port = port or 2020
        self.pidfile = pidfile or '/tmp/webdriver_{0}_{1}.pid'.format(self.host, self.port)
        self.logfile = logfile or '/tmp/webdriver_{0}_{1}.log'.format(self.host, self.port)
        self.cache = cache or os.path.join(os.path.expanduser('~'), 'webdriver.cache')
        self.nodaemon = nodaemon or False
        self.debug = debug
        init_log(self.logfile, self.nodaemon, self.debug)


    def run(self):
        log.debug('Starting WebDriver on "{0}:{1}", pidfile "{2}"'.format(self.host, self.port, self.pidfile))

        if self.shutdown():
            if not self.nodaemon:
                self.daemonize()

            # make pid
            file(self.pidfile, 'wb').write(str(os.getpid()))
            atexit.register(self.delete_pid)

            drivers = Kernel(self.cache)

            @error(500)
            def error500(error):
                return 'Internal Server Error'

            @error(404)
            def error404(error):
                return 'Not Found'

            @get('/<token:re:[a-f0-9]{32}>')
            def check(token):
                print token
                return 'OK TOKEN: ' + token

            @post('/execute')
            def handle():
                try:
                    tasks = json.loads(str(request.params.tasks))
                except Exception, e:
                    raise HTTPResponse(body=str(e), status=400)
                else:
                    if not isinstance(tasks, list):
                        raise HTTPResponse(body=str('Expect list'), status=400)

                    params = []
                    for task in tasks:
                        if 'driver' not in task:
                            raise HTTPResponse(body=str('Driver not found'), status=400)

                        if 'method' not in task:
                            raise HTTPResponse(body=str('Method not found'), status=400)

                        if 'args' in task and not isinstance(task['args'], list):
                            raise HTTPResponse(body=str('Unknown args'), status=400)

                        if 'kwargs' in task and not isinstance(task['kwargs'], dict):
                            raise HTTPResponse(body=str('Unknown kwargs'), status=400)

                        params.append({'driver': task['driver'], 'method': task['method'], 'args': task.get('args', []), 'kwargs': task.get('kwargs', {})})

                    response = drivers.execute(params)
                    if isinstance(response, int):
                        msg = HTTP_CODES.get(response, 'Unknown error')
                        raise HTTPResponse(body=msg, status=response)
                    elif isinstance(response, (tuple, list)):
                        raise HTTPResponse(body=response[1], status=response[0])
                    else:
                        return json.dumps(response)

            log.info('WebDriver started on "{0}:{1}", pidfile "{2}"'.format(self.host, self.port, self.pidfile))
            run(host=self.host, port=self.port, debug=self.debug)


    def daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                os._exit(0)
        except OSError:
            os._exit(1)

        os.chdir("/")
        os.setsid()
        os.umask(0)

        try:
            pid = os.fork()
            if pid > 0:
                os._exit(0)
        except OSError:
            os._exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file('/dev/null', 'r')
        so = file('/dev/null', 'a+')
        se = file('/dev/null', 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())


    def shutdown(self):
        try:
            pid = str(int(file(self.pidfile, 'rb').read().strip()))
        except:
            return True
        else:

            log.debug('The previous PID found, PID: {0}'.format(pid))

            def ps(pid, deadline):
                while time.time() < deadline:
                    used = subprocess.Popen('ps ' + pid, shell=True, stdout=subprocess.PIPE, close_fds=True).stdout.readlines()
                    if len(used) > 1:
                        time.sleep(0.2)
                    else:
                        return False
                return True

            if ps(pid, time.time() + 15.0):
                log.debug('Trying to send the signal SIGTERM, PID: {0}'.format(pid))
                os.kill(int(pid), signal.SIGTERM)
                if ps(pid, time.time() + 15.0):
                    log.debug('Trying to send the signal SIGKILL, PID: {0}'.format(pid))
                    os.kill(int(pid), signal.SIGKILL)
                    if ps(pid, time.time() + 15.0):
                        log.debug('We have zombie, PID: {0}'.format(pid))
                        return False
                    else:
                        log.debug('The previous WebDriver killed, PID: {0}'.format(pid))
                else:
                    log.debug('The previous WebDriver terminated, PID: {0}'.format(pid))

            return True

    def delete_pid(self):
        try:
            os.unlink(self.pidfile)
        except:
            pass