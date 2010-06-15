#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
import sys
import urlparse
from optparse import OptionParser
from primitive.fetchtool.commands import FetchCommand

parser = OptionParser(usage='usage: %prog [options] URI')
parser.add_option('-d', dest='dest', help='Destination directory')
parser.add_option('-f', dest='force', help='Overwrite if destination exists', default=False, action='store_true')
parser.add_option('-m', dest='mirror', help='Mirror URI', default=False, action='store_true')

(options, args) = parser.parse_args()

if not args:
    sys.exit('No source URI provided.')

uri = args[0]
fetchdir = options.mirror
destdir = options.dest
if not destdir:
    destdir = '.'
overwrite = options.force
protocol = urlparse.urlparse(uri)[0]
fc = FetchCommand(uri=uri, fetchdir=fetchdir, destdir=destdir, overwrite=overwrite)
fc.execute()
