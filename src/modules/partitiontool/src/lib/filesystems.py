#!/usr/bin/env python
# $Id$
#
# Kusu Partition Tool Filesystems module.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
from struct import *

class FilesystemViewer(object):
    name = 'None'
    def match(cls, buf):
        pass
    match = classmethod(match)

class Ext2Viewer(FilesystemViewer):
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


def convertUUIDToStr(bytes):
    s = ('%02x'*16) % tuple(map(ord, bytes))
    return '%s-%s-%s-%s-%s' % (s[:8], s[8:12], s[12:16], s[16:20], s[20:])
