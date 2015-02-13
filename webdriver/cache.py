# -*- coding: utf-8 -*-

__author__ = 'HAL9000'
__all__ = ['Cache']

import pickle
import sqlite3
import threading

class Cache:
    def __init__(self,  cache):
        self.lock = threading.Lock()
        self.db = sqlite3.connect(cache)
        try:
            self.db.execute('SELECT token from cache limit 1').fetchall()
        except sqlite3.OperationalError, e:
            if str(e) != 'no such table: cache':
                raise
            else:
                self.db.execute('pragma auto_vacuum=1')
                self.db.commit()
                self.db.execute('create table cache(token varchar(255) unique, expire integer, data blob)')
                self.db.commit()

    def get(self, keys, prefix):
        if not isinstance(keys, (tuple, list)):
            keys = [keys]
        result = {}
        prefix += ':'
        self.lock.acquire()
        try:
            res = self.db.execute('select token, data from cache where ' + ' or '.join(5*['token=?']), [''.join([prefix, x]) for x in keys]).fetchall()
        except:
            pass
        else:
            # TODO: тут что-то...
            print res
            for r in res:
                print r
        self.lock.release()
        found, notfound = {}, []
        for key in keys:
            if key in result:
                found[key] = result[key]
            else:
                notfound.append(key)
        return found, notfound

    def set(self, data, prefix):
        query = [(''.join([prefix, k]), v[0], sqlite3.Binary(pickle.dumps(v[1], -1))) for k, v in data.items()]
        self.lock.acquire()
        try:
            self.db.executemany('replace into cache(token, timeout, data) values(?,?,?)', query)
        except:
            res = False
        else:
            res = True
        self.lock.release()
        return res

