#!/usr/bin/env python
# $Id: helper.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
''' Helper functions for Fetchtool:
    - checkForRequiredArgs
    - isDestWritable
'''
import md5
import shutil
import urlparse
import subprocess
from path import path
from primitive.core.errors import FetchException

def matchFileMD5SUM(md5sum, infile):
    ''' Check if the file's MD5SUM matches the one given.
    '''
    f = open(infile)
    m = md5.new()
    buf = f.read(8096)
    while buf:
        m.update(buf)
        buf = f.read(8096)
    return m.hexdigest() == md5sum


def checkForRequiredArgs(input_dict, required_args):
    ''' Ensure that required arguments are present in the input
        dictionary.
    '''
    missing = filter(lambda x: x not in input_dict.keys(), required_args)
    if not missing:
        return True, []
    else:
        return False, missing


def isDestWritable(dest, fetch_dir, overwrite):
    ''' Is destination writable, given:
        * destination dir
        * the type of fetch operation
        * overwrite flag
    '''
    dest = path(dest)
    if not fetch_dir:
        if dest.exists() and not overwrite:
            return False
    return True


def decipherWgetErrors(src_uri, wget_stderr_arr):
    ''' Decipher errors from wget's stderr output.
    '''
    errors = []
    for i,e in enumerate(wget_stderr_arr):
        if e.startswith(src_uri) or e.endswith(src_uri):
            errors.append(e.strip() + ' ' + wget_stderr_arr[i+1].strip())
    if errors:
        raise FetchException, errors


def checkUserPassFormat(uri):
    ''' Check URI for a user/password pair. e.g., http://user:pass@somewhere/
        Returns True if:
        * the correct format exists.
        * no user AND password are given.
        Returns False if:
        * incomplete user/password pair is given.
        NOTE: THIS FUNCTION DOES NOT ACTUALLY DO THE AUTHENTICATION.
    '''
    s = urlparse.urlparse(uri)[1]
    try:
        userpass, host = s.split('@') # throws ValueError if
                                      # split doesn't unpack
        if len(userpass.split(':')) != 2:
            return False
    except ValueError:
        # URI given does not specify a user:password authentication.
        pass
    return True


def copyDir(src_dir, dest_dir, recursive, overwrite):
    ''' Copy a source directory to a destination.
        arguments:
            - recursive: True or False
            - overwrite: True = overwrite destination file if
                                if already exists.
                         False = silently skip copying a file
                                 if the destination already exists.
        Note:
        In recursive, the behaviour is same as
            'find . | cpio -mpdu <dest>'.
        In non-recursive, the behaviour is same as
            'find . -maxdepth 1 | cpio -mpdu <dest>'.

        If overwrite is False, then the 'u' is dropped off the cpio option.
    '''
    # taken from <unistd.h> for file/dirs access modes
    # these can be OR'ed together.
    R_OK = 4 # test for read permission.
    W_OK = 2 # test for write permission.
    X_OK = 1 # test for execute permission.

    # convert paths to be absolute.
    src_path = path(src_dir).abspath()
    dest_path = path(dest_dir).abspath()

    if not src_path.exists():
        raise IOError, "Source directory does not exist!"

    # create the dest directory if it doesn't exist initially.
    if not dest_path.exists():
        if dest_path.parent.access(R_OK|W_OK):
            dest_path.mkdir()
        else:
            raise IOError, "No read/write permission in parent directory!"
    elif not dest_path.access(R_OK|W_OK):
        raise IOError, "no read/write permission in destination directory!"

    # add the 'u' option to cpio for overwrite.
    if overwrite:
        cpio_options = '-mpdu'
    else:
        cpio_options = '-mpd'

    # use regular find if recursive
    if recursive:
        find_args = ['find', '.']
    else:
        find_args = ['find', '.', '-maxdepth', '1']

    # pipe find's output to cpio
    find = subprocess.Popen(find_args, cwd=src_path,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    cpio = subprocess.Popen(['cpio', cpio_options, '--quiet',
                             str(dest_dir)],
                            cwd=src_path,
                            stdin=find.stdout,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    cpio.communicate()
    return cpio.returncode
