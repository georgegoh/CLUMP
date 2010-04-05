#!/usr/bin/env python
# $Id: filesystems.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
"""Filesystem meta-information viewers."""
from struct import *
from primitive.support.util import convertUUIDToStr

class FilesystemViewer(object):
    name = 'None'
    def match(cls, buf):
        pass
    match = classmethod(match)

class Ext2Viewer(FilesystemViewer):
    """ This class probes the label and UUID of a ext2 filesystem.
        Example:
            >>> sda1 = Ext2Viewer('/dev/sda1')
            >>> sda1.uuid
            '0f646aa9-9a0d-4b73-86fe-a31179b9b7a0'
            >>> sda1.label
            '/boot'
    """
    sb_offset = 1024
    sb_len = 200

    def __init__(self, path):
        f = open(path)
        try:
            buf = f.read(self.sb_offset + self.sb_len)
        finally:
            f.close()

        if not self.match(buf):
            raise Exception, "FS doesn't match"
        self.superblock = buf[1024:]
        # set label.
        label = self.superblock[120:136]
        self.label = label.strip('\x00')
        # set UUID.
        uuid_bytes = self.superblock[104:120]
        self.uuid = convertUUIDToStr(uuid_bytes)        

    def match(cls, buf):
        superblock = buf[1024:]
        if superblock[56:58] == 'S\xef':
            return True
        return False
    match = classmethod(match)
