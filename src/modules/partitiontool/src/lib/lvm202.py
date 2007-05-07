#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Partition Tool LVM module.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
import subprocess
from kusuexceptions import *
from kusu.util.log import getKusuLog

logger = getKusuLog('lvm202')

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
    logger.debug('Data list from %s: %s' % (command, data_list))
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


def runCommand(command):
    logger.debug('runCommand called with command: %s' % command)
    p = subprocess.Popen(command,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    logger.debug('"%s" output: %s' %(command, out))
    logger.debug('"%s" errors: %s' %(command, err))
    return (out, err)


def createPhysicalVolume(partition_path):
    out, err = runCommand('lvm pvcreate %s' % partition_path)

def removePhysicalVolume(partition_path):
    if not physicalVolumeInUse(partition_path):
        out, err = runCommand('lvm pvremove %s' % partition_path)

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

    raise NotPhysicalVolumeError


def createVolumeGroup(vg_name, extent_size='32M', pv_path_list=[]):
    out, err = runCommand('lvm vgcreate %s -s %s %s' % 
                            (vg_name,
                             extent_size,
                             ' '.join(pv_path_list)))


def extendVolumeGroup(vg_name, partition_path):
    out, err = runCommand('lvm vgextend %s %s' % (vg_name, partition_path))


def reduceVolumeGroup(vg_name, partition_path):
    out, err = runCommand('lvm vgreduce %s %s' % (vg_name, partition_path))


def removeLogicalVolumeGroup(vg_name):
    out, err = runCommand('lvm vgremove %s' % vg_name)


def createLogicalVolume(vg_name, lv_name, lv_size):
    out, err = runCommand('lvm lvcreate -L%s -n%s %s' % (lv_size, lv_name, vg_name))


def removeLogicalVolume(lv_path):
    out, err = runCommand('lvm lvremove %s' % lv_path)
