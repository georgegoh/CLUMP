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

def retrieveLVMEntityData(command, field):
    display = subprocess.Popen(command,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    grep = subprocess.Popen("grep '%s'" % field,
                            shell=True,
                            stdin=display.stdout,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    awk = subprocess.Popen("awk '{ print $3 }'",
                           shell=True,
                           stdin=grep.stdout,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    result = awk.communicate()[0]
    data_list = result.strip().split('\n')
    while '' in data_list:
        data_list.remove('')
    return data_list


def retrievePhysicalVolumePaths():
    return retrieveLVMEntityData('lvm pvdisplay', 'PV Name')


def retrieveLogicalVolumeGroupNames():
    return retrieveLVMEntityData('lvm vgdisplay', 'VG Name')


def retrieveLogicalVolumePaths():
    return retrieveLVMEntityData('lvm lvdisplay', 'LV Name')


def probeLVMEntity(command, probe_dict):
    probe_result_dict = {}
    probe_command = subprocess.Popen(command,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
    probe_str = probe_command.stdout.read()
    probe_lines = probe_str.strip().split('\n')
    for line in probe_lines:
        for k,v in probe_dict.iteritems():
            if line.find(v) >= 0:
                echo = subprocess.Popen('echo %s' % line,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                awk = subprocess.Popen("awk '{ print $3 }'",
                                       shell=True,
                                       stdin=echo.stdout,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
                value = awk.communicate()[0]
                probe_result_dict[k] = value.strip()
                if not probe_result_dict[k]:
                    probe_result_dict[k] = None
    return probe_result_dict


def probePhysicalVolume(path):
    probe_dict = { 'group' : 'VG Name' }
    return probeLVMEntity('lvm pvdisplay %s' % path, probe_dict)


def probeLogicalVolumeGroup(name):
    probe_dict = { 'extent_size' : 'PE Size' }
    results_dict = probeLVMEntity('lvm vgdisplay %s --units b' % name, probe_dict)
    extent = long(results_dict['extent_size'])
    if extent < (1024*1024):
        extent = extent / 1024
        results_dict['extent_size'] = str(extent) + 'K'
    else:
        extent = extent / 1024 / 1024
        results_dict['extent_size'] = str(extent) + 'M'
    return results_dict


def probeLogicalVolume(path):
    probe_dict = { 'group' : 'VG Name',
                   'extents' : 'Current LE' }
    return probeLVMEntity('lvm lvdisplay %s' % path, probe_dict)


def createPhysicalVolume(partition_path):
    p = subprocess.Popen('lvm pvcreate %s' % partition_path,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out = p.stdout.read()
    err = p.stderr.read()
    print 'Out: ', out
    print 'Err: ', err

def removePhysicalVolume(partition_path):
    if not physicalVolumeInUse(partition_path):
        p = subprocess.Popen('lvm pvremove %s' % partition_path,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out = p.stdout.read()
        err = p.stderr.read()
        print 'Out: ', out
        print 'Err: ', err

def physicalVolumeInUse(path):
    p = subprocess.Popen('lvm pvdisplay %s' % path,
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
         

def createVolumeGroup(vg_name, extent_size='32M', pv_path_list=[]):
    p = subprocess.Popen('lvm vgcreate %s -s %s %s' % 
                            (vg_name,
                             extent_size,
                             ' '.join(pv_path_list)),
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out = p.stdout.read()
    err = p.stderr.read()
    print 'Out: ', out
    print 'Err: ', err


def extendVolumeGroup(vg_name, partition_path):
    p = subprocess.Popen('lvm vgextend %s %s' % (vg_name, partition_path),
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out = p.stdout.read()
    err = p.stderr.read()
    print 'Out: ', out
    print 'Err: ', err


def reduceVolumeGroup(vg_name, partition_path):
    p = subprocess.Popen('lvm vgreduce %s %s' % (vg_name, partition_path),
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out = p.stdout.read()
    err = p.stderr.read()
    print 'Out: ', out
    print 'Err: ', err


def createLogicalVolume(vg_name, lv_name, lv_size):
    p = subprocess.Popen('lvm lvcreate -L%d -n%s %s' % (lv_size, lv_name, vg_name),
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out = p.stdout.read()
    err = p.stderr.read()
    print 'Out: ', out
    print 'Err: ', err


def removeLogicalVolume(lv_path):
    p = subprocess.Popen('lvm lvremove %s' % lv_path,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out = p.stdout.read()
    err = p.stderr.read()
    print 'Out: ', out
    print 'Err: ', err
