#!/usr/bin/env python
#
# $Id$
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#

import os
import sys
from path import path

KUSU_GLOBAL_LOCK_FILE = path('/var/lock/subsys/kusu')

class KusuGlobalLock(object):
    """Implements a global locking mechanism for Kusu tools.

    kitops will use this to acquire a global lock while a native
    base kit upgrade is in progress. All Kusu tools should refuse to
    run while this lock is in place. Once kitops has completed its
    upgrade task, it will release the lock. If kitops encountered
    an exception, it must make sure that the lock is released.
    """

    def __init__(self):
        self._token = None
        self._lock_file = KUSU_GLOBAL_LOCK_FILE

    def is_locked(self):
        return self._lock_file.exists()

    def _create_lock_file(self):
        self._token = os.urandom(32).encode('hex')
        if not self._lock_file.parent.exists():
            self._lock_file.parent.makedirs()
        self._lock_file.write_text(self._token)

    def acquire(self):
        if self.is_locked():
            return False
        self._create_lock_file()
        return True

    def release(self):
        if self.is_locked() and self._token == self._lock_file.text():
            self._lock_file.remove()
            return True
        return False


def check_for_global_lock():
    if KusuGlobalLock().is_locked():
        msg = ('ERROR: Native base kit upgrade in progress. Please try running '
               'this tool after the upgrade has completed.\n')
        sys.stderr.write(msg)
        sys.exit(1)


if __name__ == "__main__":
    lock = KusuGlobalLock()

    # Normal usage
    assert not lock.is_locked()
    assert lock.acquire()
    assert KUSU_GLOBAL_LOCK_FILE.exists()
    assert lock.is_locked()
    assert is_globally_locked()
    assert lock.release()
    assert not KUSU_GLOBAL_LOCK_FILE.exists()

    # If it's not locked, release returns False.
    assert not lock.is_locked()
    assert not lock.release()

    # If I've previously locked it, performing another acquire
    # should return False.
    assert lock.acquire()
    assert not lock.acquire()
    assert lock.release()

    # Should not be able to release a lock I do not own.
    rogue_lock = KusuGlobalLock()
    assert lock.acquire()
    assert not rogue_lock.release()
    assert lock.release()

