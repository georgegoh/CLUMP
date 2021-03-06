#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
"""The functions in this module(lvm202) abstract away the details of calling
the 'lvm' commands away from the lvm module, which handles the logical 
manipulation of LVM entities. This module is written to make use of LVM version
2.02"""
from errors import *
try: import subprocess
except: from popen5 import subprocess

import primitive.support.log as primitivelog
primitivelog.setLoggerClass()
logger = primitivelog.getPrimitiveLog(name='lvm202.py')
logger.addFileHandler()

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
    result = grep.communicate()[0].split('\n')
    data_list = []
    for line in result:
        data_list.append(getValue(line, field))

    while '' in data_list:
        data_list.remove('')

    logger.debug('Data list from %s: %s' % (command, data_list))
    return data_list

def getValue(line, field):
    i = line.find(field)
    i = i + len(field)
    value = line[i:].strip()
    return value

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
    logger.debug(probe_command.stderr.read())
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
    results_dict = {}
    out, err = subprocess.Popen(['lvm', 'vgdisplay', '-c', name],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE).communicate()

    if not out:
        # if there are no volume groups, return a default value.
        results_dict['extent_size'] = '0M'
        results_dict['extents_free'] = 0L
        return results_dict

    out_list = out.split(':')

    # parse extent size to human-readable strings
    extent = long(out_list[12])
    if extent < (1024*1024):
        extent = extent / 1024
        results_dict['extent_size'] = str(extent) + 'K'
    else:
        extent = extent / 1024 / 1024
        results_dict['extent_size'] = str(extent) + 'M'

    # parse free extents
    results_dict['extents_free'] = long(out_list[15])
    return results_dict


def probeLogicalVolume(path):
    probe_dict = { 'group' : 'VG Name',
                   'extents' : 'Current LE' }
    return probeLVMEntity('lvm lvdisplay %s' % path, probe_dict)


def runCommand(command):
    logger.info('runCommand called with command: %s' % command)
    p = subprocess.Popen(command,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    logger.info('"%s" output: %s' %(command, out))
    logger.info('"%s" errors: %s' %(command, err))
    return (out, err)


def createPhysicalVolume(partition_path):
    out, err = runCommand('lvm pvcreate %s -ff -y' % partition_path)
    return (out, err)

def removePhysicalVolume(partition_path):
    if not physicalVolumeInUse(partition_path):
        out, err = runCommand('lvm pvremove %s' % partition_path)
        return (out, err)

def physicalVolumeInUse(path):
    out, err = runCommand('lvm pvdisplay %s' % path)
    allocated = -1
    if out:
        out_line = out.split('\n')
        for line in out_line:
            if line.find('Allocated PE') != -1:
                 allocated = int(line.split()[2])
    if allocated == 0:
        return False
    elif allocated > 0:
        return True

    raise NotPhysicalVolumeError, '%s is not a LVM physical volume' % path


def createVolumeGroup(vg_name, extent_size='32M', pv_path_list=[]):
    out, err = runCommand('lvm vgcreate %s -s %s %s' % 
                            (vg_name,
                             extent_size,
                             ' '.join(pv_path_list)))
    return (out, err)

def extendVolumeGroup(vg_name, partition_path):
    out, err = runCommand('lvm vgextend %s %s' % (vg_name, partition_path))
    return (out, err)

def reduceVolumeGroup(vg_name, partition_path):
    out, err = runCommand('lvm vgreduce %s %s' % (vg_name, partition_path))
    return (out, err)

def removeVolumeGroup(vg_name):
    out, err = runCommand('lvm vgremove %s' % vg_name)
    return (out, err)

def activateAllVolumeGroups():
    out, err = runCommand('lvm vgchange -ay')
    return (out, err)

def createLogicalVolume(vg_name, lv_name, lv_extents, fill=False):
    extents_free = probeLogicalVolumeGroup(vg_name)['extents_free']
    if fill or lv_extents >= extents_free:
        lv_extents = extents_free
    if lv_extents > 0:
        out, err = runCommand('lvm lvcreate -l%d -n%s %s' % (lv_extents, lv_name, vg_name))
        return (out, err)
    else:
        return '',''

def extendLogicalVolume(lv_path, new_extents, extent_size, fs_type):
    out, err = runCommand('lvm lvextend -l%d %s' % (new_extents, lv_path))
    if fs_type == 'ext2' or fs_type == 'ext3':
        size_MB = new_extents * extent_size / 1024 / 1024
        size_str = str(size_MB) + 'M'
        out, err = runCommand('e2fsck -f %s' % lv_path)
        out, err = runCommand('resize2fs %s' % lv_path)
    elif fs_type == 'reiserfs':
        size_MB = new_extents * extent_size / 1024 / 1024
        size_str = str(size_MB) + 'M'
        out, err = runCommand('reiserfsck -f %s' % lv_path)
        out, err = runCommand('resize_reiserfs %s' % lv_path)

    return (out, err)

def reduceLogicalVolume(lv_path, new_extents, extent_size, fs_type):
    if fs_type == 'ext2' or fs_type == 'ext3':
        size_MB = new_extents * extent_size / 1024 / 1024
        size_str = str(size_MB) + 'M'
        out, err = runCommand('resize2fs %s %s' % (lv_path, size_str))
    out, err = runCommand('lvm lvreduce -l%d %s -f' % (new_extents, lv_path))
    if fs_type == 'reiserfs':
        size_MB = new_extents * extent_size / 1024 / 1024
        size_str = str(size_MB) + 'M'
        out, err = runCommand('resize_reiserfs %s %s' % (lv_path, size_str))
    out, err = runCommand('lvm lvreduce -l%d %s -f' % (new_extents, lv_path))

    return (out,err)

def removeLogicalVolume(lv_path):
    out, err = runCommand('lvm lvremove -f %s' % lv_path)
    return (out, err)

def makeNodes():
    out, err = runCommand('lvm vgmknodes')
    return (out, err)
