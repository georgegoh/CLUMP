#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Partition Tool LVM module.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
__version__ = "$Revision: 268 $"
import subprocess
from kusuexceptions import *
#from kusu.util.log import Logger


def createPhysicalVolume(partition_path):
    p = subprocess.Popen('pvcreate %s' % partition_path,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out = p.stdout.read()
    err = p.stderr.read()
    print 'Out: ', out
    print 'Err: ', err

def removePhysicalVolume(partition_path):
    if not physicalVolumeInUse(partition_path):
        p = subprocess.Popen('pvremove %s' % partition_path,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out = p.stdout.read()
        err = p.stderr.read()
        print 'Out: ', out
        print 'Err: ', err

def physicalVolumeInUse(path):
    p = subprocess.Popen('pvdisplay %s' % path,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    allocated = -1
    out = p.stdout.read()
    if out:
        out_line = out.split('\n')
        for line in out_line:
            if line.find('Allocated PE') != -1:
                 allocated = int(line.split()[2])
    if allocated == 0:
        return False
    elif allocated > 0:
        return True

    raise NotPhysicalVolumeError
         

def createVolumeGroup(vg_name, pv_path_list):
    p = subprocess.Popen('vgcreate %s %s' % (vg_name, ' '.join(pv_path_list)),
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out = p.stdout.read()
    err = p.stderr.read()
    print 'Out: ', out
    print 'Err: ', err


def extendVolumeGroup(vg_name, partition_path):
    p = subprocess.Popen('vgextend %s %s' % (vg_name, partition_path),
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out = p.stdout.read()
    err = p.stderr.read()
    print 'Out: ', out
    print 'Err: ', err


def reduceVolumeGroup(vg_name, partition_path):
    p = subprocess.Popen('vgreduce %s %s' % (vg_name, partition_path),
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out = p.stdout.read()
    err = p.stderr.read()
    print 'Out: ', out
    print 'Err: ', err


def createLogicalVolume(vg_name, lv_name, lv_size):
    p = subprocess.Popen('lvcreate -L%d -n%s %s' % (lv_size, lv_name, vg_name),
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out = p.stdout.read()
    err = p.stderr.read()
    print 'Out: ', out
    print 'Err: ', err


def removeLogicalVolume(lv_path):
    p = subprocess.Popen('lvremove %s' % lv_path,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out = p.stdout.read()
    err = p.stderr.read()
    print 'Out: ', out
    print 'Err: ', err
