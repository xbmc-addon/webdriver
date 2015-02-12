# -*- coding: utf-8 -*-

import sys
import time

from fabric.api import local, run, put, sudo, env

def replace(filename, f, t):
    text = file(filename, 'rb').read().replace(f, t)
    file(filename, 'wb').write(text)


def build_sdist(version):
    local('rm -rf ./build-sdist')
    local('mkdir -p ./build-sdist/webdriver/webdriver')
    local('cp -R ./webdriver/* ./build-sdist/webdriver/webdriver/')
    local('cp ./setup.py ./build-sdist/webdriver/')
    replace('./build-sdist/webdriver/setup.py', 'version="0"', 'version="' + version + '"')
    replace('./build-sdist/webdriver/webdriver/__init__.py', 'version = "0"', 'version = "' + version + '"')
    replace('./build-sdist/webdriver/webdriver/__init__.py', 'version_info = (0,)', 'version_info = "' + ', '.join([str(int(x)) for x in version.split('.')]) + '"')
    local('cd ./build-sdist/webdriver/;python setup.py sdist')
    return './build-sdist/webdriver/dist/webdriver-' + version + '.tar.gz'


def test():
    env.host_string = '172.20.20.248'
    env.user = 'vagrant'
    env.password = 'vagrant'
    version = time.strftime('%Y.%m.%d.%H.%M.%S', time.localtime())
    filename = build_sdist(version)
    run('rm -rf /tmp/webdriver;mkdir /tmp/webdriver')
    put(filename, '/tmp/webdriver/webdriver.tar.gz')
    local('rm -rf ./build-sdist')
    run('cd /tmp/webdriver;tar zxf ./webdriver.tar.gz')
    sudo('cd /tmp/webdriver/webdriver-' + version + '/;python setup.py install;rm -rf /tmp/webdriver')
    run("""rm -rf /tmp/testrepo;mkdir -p /tmp/testrepo/repo/test_driver;echo '# -*- coding: utf-8 -*-\n__all__=["test_driver"]\nimport test_driver' > /tmp/testrepo/repo/__init__.py""")
    put('./test.py', '/tmp/testrepo/repo/test_driver/__init__.py')



def release():
    pass


def main():
    if sys.argv[1] == 'test':
        test()
    elif sys.argv[1] == 'release':
        release()


if __name__ == '__main__':
    main()
