# -*- coding: utf-8 -*-

__author__ = 'HAL9000'
__all__ = ['Run']

import argparse
import atexit
import os
import sys
import signal
import subprocess
import time


class Run:
    def __init__(self, version):
        self.version = version

    def run(self):
        args = self.args()
        if args.command == 'server':
            Daemon(self.version, args).run()

    def args(self):
        parser = argparse.ArgumentParser(description="WebDriver is a scrapers server.", add_help=False, version=self.version)
        parser.add_argument ('-?', '--help', action='help', help='Help')
        subparsers = parser.add_subparsers(dest='command')

        server = subparsers.add_parser('server', add_help=False)
        server.add_argument('-R', '--repo', dest='repo', help='Path to repository with plugins')
        server.add_argument('-P', '--pid', dest='pid', help='Path to file PID')
        server.add_argument('-L', '--log', dest='log', help='Path to log')
        server.add_argument('-C', '--cache', dest='cache', help='Path to cache')
        server.add_argument('-h', '--host', dest='host', help='Server host')
        server.add_argument('-p', '--port', dest='port', help='Server port', type=int)
        server.add_argument('-n', '--nodaemon', dest='nodaemon', help='Runs WebDriver process in standalone mode', action='store_true')
        server.add_argument('-d', '--debug', dest='debug', help='Runs WebDriver in debug mode', action='store_true')
        server.add_argument ('-?', '--help', action='help', help='Help')

        return parser.parse_args()


class Daemon:
    def __init__(self, version, args):
        self.version = version

        self.host = args.host or '0.0.0.0'
        self.port = args.port or 2020
        self.nodaemon = args.nodaemon or False
        self.debug = args.debug or False

        self.repo = self.make_path(args.repo, os.path.join('repo', ''))
        self.pid = self.make_path(args.pid, 'webdriver.pid')
        self.cache = self.make_path(args.cache, 'webdriver.cache')
        self.log = self.make_path(args.log, os.path.join('logs', 'webdriver.log'))


    def make_path(self, path, default):
        if path:
            return path
        path = os.path.join(os.path.expanduser('~'), 'webdriver', default)
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        return path


    def run(self):
        if self.shutdown():
            self.dlog('Starting WebDriver on "{0}:{1}", pid "{2}"'.format(self.host, self.port, self.pid))

            if not self.nodaemon:
                self.daemonize()

            # make pid
            file(self.pid, 'wb').write(str(os.getpid()))
            atexit.register(self.delete_pid)

            from .log import make_log
            make_log(self.log, self.nodaemon, self.debug)

            from .server import Server
            Server(self.version, self.host, self.port, self.repo, self.cache, self.debug).start()


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
            pid = str(int(file(self.pid, 'rb').read().strip()))
        except:
            return True
        else:

            self.dlog('The previous PID found, PID: {0}'.format(pid))

            def ps(pid, deadline):
                while time.time() < deadline:
                    used = subprocess.Popen('ps ' + pid, shell=True, stdout=subprocess.PIPE, close_fds=True).stdout.readlines()
                    if len(used) > 1:
                        time.sleep(0.2)
                    else:
                        return False
                return True

            if ps(pid, time.time() + 15.0):
                self.dlog('Trying to send the signal SIGTERM, PID: {0}'.format(pid))
                os.kill(int(pid), signal.SIGTERM)
                if ps(pid, time.time() + 15.0):
                    self.dlog('Trying to send the signal SIGKILL, PID: {0}'.format(pid))
                    os.kill(int(pid), signal.SIGKILL)
                    if ps(pid, time.time() + 15.0):
                        self.dlog('We have zombie, PID: {0}'.format(pid))
                        return False
                    else:
                        self.dlog('The previous WebDriver killed, PID: {0}'.format(pid))
                else:
                    self.dlog('The previous WebDriver terminated, PID: {0}'.format(pid))

            return True

    def delete_pid(self):
        try:
            os.unlink(self.pid)
        except:
            pass

    def dlog(self, msg):
        if self.debug:
            print msg