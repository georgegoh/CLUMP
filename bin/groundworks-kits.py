#!/usr/bin/env python
# Copyright (C) 2007 Platform Computing Inc
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
# $Id$
#

import os
import sys
import subprocess
import tempfile
import atexit
import shutil
import optparse
import glob
from ConfigParser import ConfigParser
import string
import commands
from time import localtime, strftime

def cleanup(workspace):
    """Housekeeping routines"""
    if os.path.exists(workspace):
        l= os.listdir(workspace)
        for f in l:
            
            if f.endswith('.cfg') or f.startswith('groundworks'):
                continue

            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.remove(f)
   
def getBuildDist():
    build_dist = os.environ.get('KUSU_BUILD_DIST', None)
      
    if not build_dist:
        if os.path.exists('/etc/redhat-release'):
            splits = open('/etc/redhat-release').readline().split()
            
            if 'centos' == splits[0].lower():
                name = splits[0]
            
            elif 'red' == splits[0].lower():
                name = 'rhel'
        
        elif os.path.exists('/etc/SuSE-release'):
            lines = open('/etc/SuSE-release').readlines()
            splits = lines[0].split()
            
            if 'suse' == splits[0].lower():
                name = 'sles'
        else:
            name, ver = platform.dist()[:2]
     
        build_dist = name
 
    return build_dist.lower()
    
def checkoutSource(repository, revision, workspace):
    if revision==None:
        cmd = "svn co %s %s" % (repository,workspace)
    else:
        cmd = "svn co --revision %s %s %s" % (revision,repository,workspace)
     
    buildP = subprocess.Popen("mkdir -p %s" % workspace ,shell=True,env=os.environ,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout, stderr = buildP.communicate()
    if buildP.returncode:
        raise IOError, stderr
    
    print "##################################################"
    print "# %s" % strftime('%a %b %d %H:%I:%S %Z %Y', localtime())
    print "# %s" % cmd
    print "##################################################"
    
    svnP = subprocess.Popen(cmd ,shell=True,cwd=None,stderr=subprocess.PIPE)
    stdout, stderr = svnP.communicate()
    if svnP.returncode:
        raise IOError, stderr
    
    if revision == None:
        svninfoP = subprocess.Popen("svn info %s | grep 'Last Changed Rev' | awk '{print $4}'" % workspace,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout, stderr = svninfoP.communicate()
        if svninfoP.returncode:
            raise IOError, stderr
        
        return stdout.strip()
    else:
        return revision
    
def getKitRevision(workspace):
    if not os.path.exists(workspace):
        print '%s not found! No such File or Directory.' % workspace
        sys.exit(-1)
    
    svninfoP = subprocess.Popen("svn info %s | grep 'Last Changed Rev' | awk '{print $4}'" % workspace,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout, stderr = svninfoP.communicate()
    if svninfoP.returncode:
        raise IOError, stderr
        
    return stdout.strip()

def buildKit(recipe,kit,workspace,values):
    if not recipe.has_section(kit):
        print 'No recipe to build %s kit!' % kit
        sys.exit(-1)
    if not os.path.exists(workspace):
        print '%s not found! No such File or Directory.' % workspace
        sys.exit(-1)
    if not recipe.has_option(kit,'build_commands'):
        print 'No commands to build %s kit.' % kit
        sys.exit(-1)
    
    for cmd in eval(recipe.get(kit,'build_commands', vars=values)):
        
        print "##################################################"
        print "# %s" % strftime('%a %b %d %H:%I:%S %Z %Y', localtime())
        print "# %s" % cmd
        print "##################################################"
        
        buildP = subprocess.Popen(cmd ,shell=True,cwd=workspace,env=os.environ,stderr=subprocess.PIPE)
        stdout, stderr = buildP.communicate()
        if buildP.returncode:
            raise IOError, stderr
    
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-r', '--recipe', dest='recipe', help="Specify the recipe file")
    parser.add_option('-f', '--force_clean_build', dest='force_clean_build', action='store_true', help="Force build from a clean checkout")
    options, args = parser.parse_args()

    if not options.recipe: 
        print 'Please specify the recipe file to build!'
        sys.exit(-1)

    if not os.path.exists(options.recipe):
        print '%s not found!' % options.recipe
        sys.exit(-1)
    
    topdir = os.getcwd()
    grdwkdir = os.path.abspath(os.path.dirname(sys.argv[0]))
  
    recipe = ConfigParser({'topdir': topdir, 'grdwkdir': grdwkdir})
    recipe.read([options.recipe])
    kits =  recipe.sections()
 
    if not kits:
        print "No section defined in the recipe"
        sys.exit(-1)
    
    kit = kits[0]
   
    # dist not defined, use system defaults
    values = {}
    if not recipe.has_option(kit, 'dist'):
        # lower case dist 
        # upper case dist
        values = {'dist':getBuildDist(), 'udist':getBuildDist().upper(), 'distsrc': os.environ.get('KUSU_DISTRO_SRC', '')}
    else:
        values = {'dist':getBuildDist(), 'udist':recipe.get(kit,'dist').upper(), 'distsrc': os.environ.get('KUSU_DISTRO_SRC', '')}
        
    if not recipe.has_option(kit, 'distarch'):
        values.update({'distarch': platform.processor()})

    if 'defaults' in recipe.sections():
        print "recipe is for building meta-data iso. Please give kits-only recipe."
        sys.exit(-1)     
            
    if recipe.getboolean(kit,'force_clean_build') or options.force_clean_build:

        cleanup(topdir)        
        print 'Checking out %s kit ..... ' % kit
        if recipe.get(kit,'build_revision') == '0':
            kit_revision = checkoutSource(recipe.get(kit,'repository'),None,topdir)
        else:
            kit_revision = checkoutSource(recipe.get(kit,'repository'),recipe.get(kit,'build_revision'),topdir)

        if kit == 'kusu':
            build_revision_file = file(os.path.join(topdir, 'build_revision'),'w')
            build_revision_file.write(kit_revision)
            build_revision_file.close()

        recipe.set(kit, 'build_revision', kit_revision)
        buildKit(recipe,kit,topdir,values)
    else:
        kit_revision = getKitRevision(topdir)

        if kit == 'kusu':
            build_revision_file = file(os.path.join(topdir, 'build_revision'),'w')
            build_revision_file.write(kit_revision)
            build_revision_file.close()
        recipe.set(kit, 'build_revision', kit_revision)
        buildKit(recipe,kit,topdir,values)        
