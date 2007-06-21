#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import sys
import os


def main():
    pass


if __name__ == '__main__':
    main()


import os
import glob
import sys
import commands
import re
# ------------------------------------------------------

def prune(items,max):
  timestamps = items.keys()
  timestamps.sort(reverse=True)

  for timestamp in timestamps[max:]:
    print items[timestamp]
    os.unlink(items[timestamp])

def getkusutgz(dir):
  items = {}
  filelist = commands.getoutput("ls -lt --time-style=+\"%Y%m%d%H%m%S\" "+dir+"/*.tgz")
  for line in filelist.splitlines()[1:]:
    fields = line.split()
    f = fields[5]+" "+fields[6]
    items[fields[5]] = fields[6]
  return items

def getkusuiso(dir):
  items = {}
  filelist = commands.getoutput("ls -lt --time-style=+\"%Y%m%d%H%m%S\" "+dir+"/*.iso")
  for line in filelist.splitlines()[1:]:
    fields = line.split()
    f = fields[5]+" "+fields[6]
    items[fields[5]] = fields[6]
  return items

def getbuildbotlogs(dir):
  items = {}
  filelist = commands.getoutput("ls -l "+dir)
  lines = filelist.splitlines()
  idx = 0
  for line in lines[1:]:
    fields = line.split()
    items[idx] = dir+"/"+fields[8]
    idx = idx + 1

  keys = items.keys()
  keys.sort(reverse=True)
  pcount = 0
  bcount = 0
  bnum = ""
  for key in keys:
    if bcount > 7:
      break
    
    build = re.findall(r"(\d+)",os.path.basename(items[key]))
    if len(build) > 0:
      if build[0] != bnum:
        bcount = bcount + 1
        bnum = build[0]
      pcount = pcount + 1
  return (items,pcount+1)


if __name__ == '__main__':
        #prune(glob.glob(dir + '/*.src.tgz'))
        #prune(glob.glob(dir + '/*.iso'))
        prune(getkusutgz('/data/scratch/fedora/6/i386'),7)
        prune(getkusuiso('/data/scratch/fedora/6/i386'),7)
        (items,max) = getbuildbotlogs('/data/buildbot/buildmaster/kusu/full')
        prune(items,max)
        
