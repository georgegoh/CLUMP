
import sys

try:
    import subprocess
except:
    from popen5 import subprocess


def display(desc):
    print '%s%s' % (' '*3, desc or ''),
    sys.stdout.flush()


def failure():
    cmd = 'source /lib/lsb/init-functions && log_failure_msg "$@"'
    failureP = subprocess.Popen(cmd,
                                shell=True)
    failureP.communicate()
    sys.stdout.flush()

def success():
    cmd = 'source /lib/lsb/init-functions && log_success_msg "$@"'
    successP = subprocess.Popen(cmd,
                                shell=True)
    successP.communicate()
    sys.stdout.flush()

def warning():
    cmd = 'source /lib/lsb/init-functions && log_warning_msg "$@"'
    successP = subprocess.Popen(cmd,
                                shell=True)
    successP.communicate()
    sys.stdout.flush()

