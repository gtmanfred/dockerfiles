#!/usr/bin/env python
from __future__ import print_function

import os
import pip
import socket
import subprocess
import sys
import threading

pip.main(['install', '/srv/gitrepo'])


class Thread(object):
    threads = []

    @classmethod
    def start(cls, saltcmd, args=None):
        cmd = [saltcmd]
        if len(sys.argv) > 1:
            cmd.extend(sys.argv[1:])
        if args is not None:
            cmd.extend(args)
        t = threading.Thread(target=subprocess.call, args=(cmd,))
        cls.threads.append(t)
        t.start()

if 'True' in (os.environ.get('SALT_MASTER', 'False'), os.environ.get('SALT_API', 'False')):
    spmdir = os.environ.get('SPM_DIR', '/srv/spms')
    spmbuilddir = os.environ.get('SPM_BUILD_DIR', '/srv/spm_build')
    if os.path.isdir(spmdir):
        for dirname in os.listdir(spmdir):
            if not os.path.isdir(os.path.join(spmdir, dirname)):
                continue
            subprocess.call(['spm', 'build', os.path.join(spmdir, dirname)])
        if os.path.isdir(spmbuilddir):
            for spmfile in os.listdir(spmbuilddir):
                subprocess.call(['spm', 'local', 'install', '-y', os.path.join(spmbuilddir, spmfile)])
    Thread.start('salt-master')
    if os.environ.get('SALT_API', 'False') == 'True':
        subprocess.call(['salt-call', '--local', 'tls.create_self_signed_cert'])
        Thread.start('salt-api')
if 'True' in (os.environ.get('SALT_MINION', 'False'), os.environ.get('SALT_PROXY', 'False')):
    minionid = '-'.join(['minion', socket.gethostname()])
    with open('/etc/salt/minion_id', 'w') as idfile:
        print(minionid, end='', file=idfile)
    Thread.start('salt-minion')
    subprocess.call(['salt-call', 'saltutil.sync_all'])
    if os.environ.get('SALT_PROXY', 'False') == 'True':
        subprocess.call(['salt-call', 'state.apply', 'proxy'])
        proxyid = '-'.join(['proxy', socket.gethostname()])
        Thread.start('salt-proxy', args=['--proxyid', proxyid])

for thread in Thread.threads:
    thread.join()
