#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import os
import time
import warnings
import logging
import sqlalchemy as sa
from sqlalchemy.ext.sessioncontext import SessionContext
from sqlalchemy.ext.assignmapper import assign_mapper
from kusu.util.errors import *
import kusu.util.log as kusulog
from primitive.system.software.dispatcher import Dispatcher

logging.getLogger('sqlalchemy').parent = kusulog.getKusuLog()

# it seems these must be told to be quiet individually...
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm.attributes').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm.attributes.InstrumentedAttribute').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm.mapper').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm.mapper.Mapper').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm.properties').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm.properties.PropertyLoader').setLevel(logging. WARNING)
logging.getLogger('sqlalchemy.orm.query').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm.query.Query').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm.strategies').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm.strategies.ColumnLoader').setLevel(logging.   WARNING)
logging.getLogger('sqlalchemy.orm.strategies.LazyLoader').setLevel(logging.     WARNING)
logging.getLogger('sqlalchemy.orm.sync').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm.sync.SyncRule').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.sql').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.sql.ClauseVisitor').setLevel(logging.WARNING)
kl = kusulog.getKusuLog('db')

# Filter out all type of warnings
# SQ warns about outdated sqlite version
warnings.simplefilter('ignore', Warning)

try:
    import subprocess
except:
    from popen5 import subprocess

class BaseTable(object):
    cols = []
    def __init__(self, **kwargs):
        for col, value in kwargs.items():
            if col not in self.cols:
                raise NoSuchColumnError, '%s not found' % col 
            else:
                setattr(self, col, value)

    # Does not work for now, since
    # SA sets some custom stuff.
    #def __getattr__(self, col, value):
    #    if col not in self.cols:
    #        raise NoSuchColumnError, '%s not found' % col 
    #    else:
    #        object.__getattr__(self, col, value)
            
    #def __setattr__(self, col, value):
    #    if col not in self.cols:
    #        raise NoSuchColumnError, '%s not found' % col 
    #    else:
    #        object.__setattr__(self, col, value)

class AppGlobals(BaseTable):
    cols = ['kname', 'kvalue', 'ngid']
    def __repr__(self):
        return '%s(%r,%r,%r)' % \
               (self.__class__.__name__, self.kname, self.kvalue, self.ngid)

class Components(BaseTable): 
    cols = ['kid', 'cname', 'cdesc', 'os', 'ctype']
    def __repr__(self):
        return '%s(%r,%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.kid, self.cname, self.os, self.ctype,
                self.cdesc)

class DriverPacks(BaseTable): 
    cols = ['dpid', 'cid', 'dpname', 'dpdesc']
    def __repr__(self):
        return '%s(%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.dpid, self.cid, self.dpname, self.dpdesc)

class Kits(BaseTable): 
    cols = ['rname', 'rdesc', 'version', \
            'isOS', 'removable', 'arch', 'osid']

    def prepNameVerArch(self, char):
        rname = ''
        version = ''
        arch = ''

        if self.rname:
            rname = self.rname

        if self.version:
            if rname:
                version = char
            version += self.version

        if self.arch:
            if rname or version:
                arch = char
            arch += self.arch
        return rname, version, arch

    def getLongName(self):
        return '%s%s%s' % self.prepNameVerArch('-') 

    longname = property(getLongName)

    def __repr__(self):
        return '%s(%r,%r,%r,%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.rname, self.version, self.arch,
               self.rdesc, self.isOS, self.osid, self.removable)

class Modules(BaseTable): 
    cols = ['ngid', 'module', 'loadorder']
    def __repr__(self):
        return '%s(%r,%r,%r)' % \
               (self.__class__.__name__, self.ngid, self.module, self.loadorder)

class Networks(BaseTable): 
    cols = ['network', 'subnet', 'device', 'suffix', \
            'gateway', 'options', 'netname', 'startip', \
            'inc', 'type', 'usingdhcp']
    types = ['public', 'provision', 'other']
    def __repr__(self):
        return '%s(%r,%r,%r,%r,%r,%r,%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.network, self.subnet,
                self.device, self.suffix, self.gateway, self.options,
                self.netname, self.startip, self.inc, self.usingdhcp)

class NGHasComp(BaseTable):
    cols = ['ngid', 'cid']
    def __repr__(self):
        return '%s(%r,%r)' % \
               (self.__class__.__name__, self.ngid, self.cid)

class NGHasNet(BaseTable):
    cols = ['ngid', 'netid']
    def __repr__(self):
        return '%s(%r,%r)' % \
               (self.__class__.__name__, self.ngid, self.netid)

class Nics(BaseTable):
    cols = ['nid', 'netid', 'mac', 'ip', 'boot']
    def __repr__(self):
        return '%s(%r,%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.nid, self.netid, self.mac,
                self.ip, self.boot)

class NodeGroups(BaseTable):
    cols = ['repoid', 'ngname', 'installtype', \
            'ngdesc', 'nameformat', 'kernel', 'initrd', \
            'kparams', 'type']
    types = ['installer', 'compute', 'other']
    def __repr__(self):
        return '%s(%r,%r,%r,%r,%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.ngname, self.repoid,
                self.installtype, self.ngdesc, self.nameformat, self.kernel,
                self.initrd, self.kparams)

class Nodes(BaseTable):
    cols = ['ngid', 'name', 'kernel', 'initrd', \
            'kparams', 'state', 'bootfrom', 'lastupdate', \
            'rack', 'rank']
    def __repr__(self):
        return '%s(%r,%r,%r,%r,%r,%r,%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.ngid, self.name, self.kernel,
                self.initrd, self.kparams, self.state, self.bootfrom, 
                self.lastupdate, self.rack, self.rank)

class Packages(BaseTable):
    cols = ['ngid', 'packagename']
    def __repr__(self):
        return '%s(%r,%r)' % \
               (self.__class__.__name__, self.ngid, self.packagename)

class Partitions(BaseTable):
    cols = ['ngid', 'device', 'partition', 'mntpnt', \
            'fstype', 'size', 'options', 'preserve']
    def __repr__(self):
        return '%s(%r,%r,%r,%r,%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.ngid, self.device, self.partition, self.mntpnt,
                self.fstype, self.size, self.options, self.preserve)

class Repos(BaseTable):
    cols = ['repoid', 'reponame', 'repository', 'installers', \
            'ostype']

    def getOS(self):
        for kit in self.kits:
             if kit.isOS:
                 return kit.os
        return None

    os = property(getOS)

    def __repr__(self):
        return '%s(%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.reponame, \
                self.repository, self.installers, self.ostype)

class ReposHaveKits(BaseTable):
    cols = ['repoid', 'kid']
    def __repr__(self):
        return '%s(%r,%r)' % \
               (self.__class__.__name__, self.repoid, self.kid)

class Scripts(BaseTable):
    cols = ['ngid', 'script']
    def __repr__(self):
        return '%s(%r,%r)' % \
               (self.__class__.__name__, self.ngid, self.script)

class OS(BaseTable):
    cols = ['osid', 'name', 'major', 'minor', 'arch']
    def __repr__(self):
        return '%s(%r,%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.osid, self.name, \
                self.major, self.minor, self.arch)

class DB(object):
    tableClasses = {'ReposHaveKits' : ReposHaveKits,
                    'AppGlobals' : AppGlobals,
                    'Components' : Components,
                    'DriverPacks' : DriverPacks,
                    'Kits' : Kits,
                    'Modules' : Modules,
                    'NGHasComp' : NGHasComp,
                    'Networks' : Networks,
                    'Nics' : Nics,
                    'NGHasNet' : NGHasNet,
                    'NodeGroups' : NodeGroups,              
                    'Nodes' : Nodes,
                    'Packages' : Packages, 
                    'Partitions' : Partitions,
                    'Scripts' : Scripts,
                    'Repos' : Repos,
                    'OS' : OS}

    __passfile = os.environ.get('KUSU_ROOT', '') + '/etc/db.passwd'

    def __init__(self, driver, db=None, username=None, password=None,
                 host='localhost', port=None, entity_name=None):
        """Initialize the database with the corrrect driver and account
           details"""

        if not db and driver == 'sqlite':
            raise NoSuchDBError, 'Must specify db for driver: %s' % driver

        if driver == 'sqlite':
            if db:
                engine_src = 'sqlite:///%s' % db
            else:
                engine_src = 'sqlite://'   # in-memory database

        elif driver == 'mysql':
            if not port:
                port = '3306'
            engine_src = 'mysql://'

            if username:
                engine_src += username
            else:
                import pwd
                engine_src += pwd.getpwuid(os.getuid())[0]

            apache_password = ''
            if username == 'apache':
                apache_password = self.__getPasswd()
            if apache_password:
                password = apache_password
                
            if password:
                engine_src += ':%s@%s:%s/%s' % (password, host, port, db)
            else:
                engine_src += '@%s:%s/%s' % (host, port, db)
 
        elif driver == 'postgres':
           if not port:
               port = '5432'
        
               engine_src = 'postgres://%s:%s@%s:%s/%s' % \
                             (username, password, host, port, db)

        else:
            raise UnsupportedDriverError, 'Invalid driver: %s' % driver

        self.driver = driver
        self.db = db
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.entity_name = entity_name
        self.ctx = None
        
        self.metadata = sa.BoundMetaData(engine_src, \
                                         poolclass=sa.pool.SingletonThreadPool)
        self._defineTables()

        # make classes available as instance attributes
        self.__dict__.update(self.tableClasses)

    def __getPasswd(self):
        """
        Open self.__passfile to retrieve password, return None on fail.
        """

        try:
            fp = file(self.__passfile, 'r')
        except IOError, msg:
            kl.error("Missing password file or insufficient privileges for " +
                     "access: %s", msg)
            return None
        except:
            kl.error("Error accessing the password file")
            return None

        cipher = fp.readline().strip()
        fp.close()
        return self.__decrypt(cipher)

    def __decrypt(self, cipher):
        #convert cipher to decrypted text
        return cipher

    def __encrypt(self):
        pass

    def dropTables(self):
        """Drops all tables in the database"""

        self.metadata.drop_all()

        # need to destroy the current session which may still contain old data
        self.ctx.del_current()
 
    def createTables(self): 
        """Creates all tables in the database"""

        self.metadata.create_all()

    def _defineTables(self):
        """Define the database schema and load 
           all mapper into class atrributes
        """
        # This originates frm the sql script.
        # Blame me for for typos
        appglobals = sa.Table('appglobals', self.metadata,
            sa.Column('agid', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('kname', sa.String(20)),
            sa.Column('kvalue', sa.String(255)),
            sa.Column('ngid', sa.Integer),
            mysql_engine='InnoDB')
        self.__dict__['appglobals'] = appglobals

        components = sa.Table('components', self.metadata,
            sa.Column('cid', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('kid', sa.Integer, sa.ForeignKey('kits.kid'), nullable=False),
            sa.Column('cname', sa.String(255)),
            sa.Column('cdesc', sa.String(255)),
            sa.Column('os', sa.String(20)),
            sa.Column('ctype', sa.String(20)),
            mysql_engine='InnoDB')
        sa.Index('components_FKIndex1', components.c.kid)
        self.__dict__['components'] = components

        driverpacks = sa.Table('driverpacks', self.metadata,
            sa.Column('dpid', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('cid', sa.Integer, sa.ForeignKey('components.cid'), nullable=False),
            sa.Column('dpname', sa.String(255)),
            sa.Column('dpdesc', sa.String(255)),
            mysql_engine='InnoDB')
        sa.Index('driverpacks_FKIndex1', driverpacks.c.cid)
        self.__dict__['driverpacks'] = driverpacks
    
        kits = sa.Table('kits', self.metadata,
            sa.Column('kid', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('rname', sa.String(45)),
            sa.Column('rdesc', sa.String(255)),
            sa.Column('version', sa.String(20)),
            sa.Column('isOS', sa.Boolean, sa.PassiveDefault('0')),
            sa.Column('removeable', sa.Boolean, sa.PassiveDefault('0')),
            sa.Column('arch', sa.String(20)),
            sa.Column('osid', sa.Integer),
            sa.ForeignKeyConstraint(['osid'], ['os.osid']),
            mysql_engine='InnoDB')
        sa.Index('kits_FKIndex1', kits.c.osid)
        self.__dict__['kits'] = kits

        modules = sa.Table('modules', self.metadata,
            sa.Column('mid', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('ngid', sa.Integer, sa.ForeignKey('nodegroups.ngid'), nullable=False),
            sa.Column('module', sa.String(45)),
            sa.Column('loadorder', sa.Integer, sa.PassiveDefault('0')),
            mysql_engine='InnoDB')
        sa.Index('modules_FKIndex1', modules.c.ngid)
        self.__dict__['modules'] = modules

        networks = sa.Table('networks', self.metadata,
            sa.Column('netid', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('network', sa.String(45)),
            sa.Column('subnet', sa.String(45)),
            sa.Column('device', sa.String(20)),
            sa.Column('suffix', sa.String(20)),
            sa.Column('gateway', sa.String(45)),
            sa.Column('options', sa.String(255)),
            sa.Column('netname', sa.String(255), unique=True),
            sa.Column('startip', sa.String(45)),
            sa.Column('inc', sa.Integer, sa.PassiveDefault('1')),
            sa.Column('type', sa.String(20), nullable=False),
            sa.Column('usingdhcp', sa.Boolean, sa.PassiveDefault('0')),
            mysql_engine='InnoDB')
        self.__dict__['networks'] = networks

        ng_has_comp = sa.Table('ng_has_comp', self.metadata,
            sa.Column('ngid', sa.Integer, primary_key=True, nullable=False),
            sa.Column('cid', sa.Integer, primary_key=True, nullable=False),
            sa.ForeignKeyConstraint(['ngid'], ['nodegroups.ngid']),
            sa.ForeignKeyConstraint(['cid'], ['components.cid']),
            mysql_engine='InnoDB')
        sa.Index('comp2ng_FKIndex1', ng_has_comp.c.cid)
        sa.Index('comp2ng_FKIndex2', ng_has_comp.c.ngid)
        self.__dict__['ng_has_comp'] = ng_has_comp
       
        # Again, this is a M-N table. 
        ng_has_net = sa.Table('ng_has_net', self.metadata,
            sa.Column('ngid', sa.Integer, primary_key=True, nullable=False),
            sa.Column('netid', sa.Integer, primary_key=True, nullable=False),
            sa.ForeignKeyConstraint(['ngid'], ['nodegroups.ngid']),
            sa.ForeignKeyConstraint(['netid'], ['networks.netid']),
            mysql_engine='InnoDB')
        sa.Index('net2ng_FKIndex1', ng_has_net.c.netid)
        sa.Index('net2ng_FKIndex2', ng_has_net.c.ngid)
        self.__dict__['ng_has_net'] = ng_has_net

        # Since nicsid is a PK, it is uniq.
        # It is reduntant to create a composite key of 
        # (nicsid | nid | netid). nid and netid can
        # just be FK and not nullable
        #
        # It may even be possible to use a mac address
        # as a PK because it should be uniq enough
        nics = sa.Table('nics', self.metadata,
            sa.Column('nicsid', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('nid', sa.Integer, sa.ForeignKey('nodes.nid'),
                      nullable=False),
            sa.Column('netid', sa.Integer, sa.ForeignKey('networks.netid'),
                      nullable=False),
            sa.Column('mac', sa.String(45), unique=True),
            sa.Column('ip', sa.String(20)),
            sa.Column('boot', sa.Boolean, sa.PassiveDefault('0')),
            mysql_engine='InnoDB')
        sa.Index('nics_FKIndex1', nics.c.nid)
        sa.Index('nics_FKIndex2', nics.c.netid)
        self.__dict__['nics'] = nics

        nodegroups = sa.Table('nodegroups', self.metadata,
            sa.Column('ngid', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('repoid', sa.Integer, sa.ForeignKey('repos.repoid'), nullable=True),
            sa.Column('ngname', sa.String(45), unique=True), 
            sa.Column('installtype', sa.String(20)),
            sa.Column('ngdesc', sa.String(255)),
            sa.Column('nameformat', sa.String(45)),
            sa.Column('kernel', sa.String(255)),
            sa.Column('initrd', sa.String(255)),
            sa.Column('kparams', sa.String(255)),
            sa.Column('type', sa.String(20), nullable=False),
            mysql_engine='InnoDB')
        sa.Index('nodegroups_FKIndex1', nodegroups.c.repoid)
        self.__dict__['nodegroups'] = nodegroups

        nodes = sa.Table('nodes', self.metadata,
            sa.Column('nid', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('ngid', sa.Integer, sa.ForeignKey('nodegroups.ngid'), nullable=False),
            sa.Column('name', sa.String(45), unique=True),
            sa.Column('kernel', sa.String(255)),
            sa.Column('initrd', sa.String(255)),
            sa.Column('kparams', sa.String(255)),
            sa.Column('state', sa.String(20)),
            sa.Column('bootfrom', sa.Boolean),
            sa.Column('lastupdate', sa.String(20)),
            sa.Column('rack', sa.Integer, sa.PassiveDefault('0')),
            sa.Column('rank', sa.Integer, sa.PassiveDefault('0')),
            mysql_engine='InnoDB')
        sa.Index('nodes_FKIndex1', nodes.c.ngid)
        self.__dict__['nodes'] = nodes

        # Not sure what is this used for.
        #
        # Could be used for third party packages that can 
        # be added to a nodegroup, an additional path
        # column will be needed. Such packages will 
        # not be in a kit or distro
        # Similar to script table. Both can be merged
        # into a single table.
        packages = sa.Table('packages', self.metadata,
            sa.Column('idpackages', sa.Integer, primary_key=True, 
                      autoincrement=True),
            sa.Column('ngid', sa.Integer, sa.ForeignKey('nodegroups.ngid'),
                      nullable=False),
            sa.Column('packagename', sa.String(255)),
            mysql_engine='InnoDB')
        sa.Index('packages_FKIndex1', packages.c.ngid)
        self.__dict__['packages'] = packages

        partitions = sa.Table('partitions', self.metadata,
            sa.Column('idpartitions', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('ngid', sa.Integer, nullable=False),
            sa.Column('device', sa.String(255)),
            sa.Column('partition', sa.String(255)),
            sa.Column('mntpnt', sa.String(255)),
            sa.Column('fstype', sa.String(20)),
            sa.Column('size', sa.String(45)),
            sa.Column('options', sa.String(255)),
            sa.Column('preserve', sa.Boolean, sa.PassiveDefault('1'), nullable=False),
            sa.ForeignKeyConstraint(['ngid'],
                                    ['nodegroups.ngid']),
            mysql_engine='InnoDB')
        sa.Index('partitions_FKIndex1', partitions.c.ngid)
        self.__dict__['partitions'] = partitions

        repos = sa.Table('repos', self.metadata,
            sa.Column('repoid', sa.Integer, primary_key=True,
                      autoincrement=True),
            sa.Column('reponame', sa.String(255), unique=True),
            sa.Column('repository', sa.String(255)),
            sa.Column('installers', sa.String(255)),
            sa.Column('ostype', sa.String(20)),
            mysql_engine='InnoDB')
        self.__dict__['repos'] = repos

        # A junction table. M-N relationship
        repos_have_kits = sa.Table('repos_have_kits', self.metadata,
            sa.Column('repoid', sa.Integer, primary_key=True),
            sa.Column('kid', sa.Integer, primary_key=True),
            sa.ForeignKeyConstraint(['repoid'], ['repos.repoid']),
            sa.ForeignKeyConstraint(['kid'], ['kits.kid']),
            mysql_engine='InnoDB')
        sa.Index('repos_has_rolls_FKIndex1', repos_have_kits.c.repoid)
        sa.Index('repos_has_kits_FKIndex2', repos_have_kits.c.kid)
        self.__dict__['repos_have_kits'] = repos_have_kits

        scripts = sa.Table('scripts', self.metadata,
            sa.Column('idscripts', sa.Integer, primary_key=True),
            sa.Column('ngid', sa.Integer, primary_key=True),
            sa.Column('script', sa.String(255)),
            sa.ForeignKeyConstraint(['ngid'],
                                    ['nodegroups.ngid']),
            mysql_engine='InnoDB')
        sa.Index('scripts_FKIndex1', scripts.c.ngid)
        self.__dict__['scripts'] = scripts

        os = sa.Table('os', self.metadata,
            sa.Column('osid', sa.Integer, primary_key=True,
                      autoincrement=True),
            sa.Column('name', sa.String(20)),
            sa.Column('major', sa.String(20)),
            sa.Column('minor', sa.String(20)),
            sa.Column('arch', sa.String(20)),
            mysql_engine='InnoDB')
        self.__dict__['os'] = os

        self._assignMappers()

    def _assignMappers(self):
        """
        Assign default mappers to respective class.
        """

        self.ctx = SessionContext(sa.create_session)
        # mappers have been created, do nothing
        from sqlalchemy.orm.mapper import ClassKey 
        if sa.orm.mapper_registry.has_key(ClassKey(ReposHaveKits, self.entity_name)):
#            self.ctx.set_current(sa.orm.mapper_registry.get(ClassKey(ReposHaveKits, self.entity_name)).get_session())
            return
        #else:

        os = sa.Table('os', self.metadata, autoload=True)
        assign_mapper(self.ctx, OS, os, entity_name=self.entity_name)

        repos_have_kits = sa.Table('repos_have_kits', self.metadata,
                                   autoload=True)
        assign_mapper(self.ctx, ReposHaveKits, repos_have_kits,
                      entity_name=self.entity_name)

        appglobals = sa.Table('appglobals', self.metadata, autoload=True)
        assign_mapper(self.ctx, AppGlobals, appglobals,
                      entity_name=self.entity_name)

        ng_has_comp = sa.Table('ng_has_comp', self.metadata, autoload=True)
        assign_mapper(self.ctx, NGHasComp, ng_has_comp,
                      entity_name=self.entity_name)

        components = sa.Table('components', self.metadata, autoload=True)
        assign_mapper(self.ctx, Components, components,
          properties={'nodegroups': sa.relation(NodeGroups,
                                                secondary=ng_has_comp,
                                                entity_name=self.entity_name),
                      'kit': sa.relation(Kits,
                                         entity_name=self.entity_name),
                    'driverpacks': sa.relation(DriverPacks,
                                        entity_name=self.entity_name)},
          entity_name=self.entity_name)

        driverpacks = sa.Table('driverpacks', self.metadata, autoload=True)
        assign_mapper(self.ctx, DriverPacks, driverpacks, entity_name=self.entity_name)

        kits = sa.Table('kits', self.metadata, autoload=True)
        assign_mapper(self.ctx, Kits, kits,
          properties={'components': sa.relation(Components,
                                                entity_name=self.entity_name),
                      'os': sa.relation(OS, entity_name=self.entity_name),
                      'removable': kits.c.removeable},
          entity_name=self.entity_name)

        modules = sa.Table('modules', self.metadata, autoload=True)
        assign_mapper(self.ctx, Modules, modules, entity_name=self.entity_name)

        networks = sa.Table('networks', self.metadata, autoload=True)
        assign_mapper(self.ctx, Networks, networks,
                      entity_name=self.entity_name)

        nics = sa.Table('nics', self.metadata, autoload=True)
        assign_mapper(self.ctx, Nics, nics,
          properties={'network': sa.relation(Networks,
                                             entity_name=self.entity_name)},
          entity_name=self.entity_name)

        ng_has_net = sa.Table('ng_has_net', self.metadata, autoload=True)
        assign_mapper(self.ctx, NGHasNet, ng_has_net,
                      entity_name=self.entity_name)

        nodegroups = sa.Table('nodegroups', self.metadata, autoload=True)
        assign_mapper(self.ctx, NodeGroups, nodegroups,
          properties={'components': sa.relation(Components,
                                                secondary=ng_has_comp,
                                                entity_name=self.entity_name),
                      'partitions': sa.relation(Partitions,
                                                entity_name=self.entity_name),
                      'networks': sa.relation(Networks, secondary=ng_has_net,
                                              entity_name=self.entity_name),
                      'nodes': sa.relation(Nodes,
                                           entity_name=self.entity_name),
                      'modules': sa.relation(Modules,
                                           entity_name=self.entity_name),
                      'packages': sa.relation(Packages,
                                           entity_name=self.entity_name)},

          entity_name=self.entity_name)

            # Currently nodegroups <-> components relationship is defined twice.
            # Possible to replace this with ingenious backref-fu.

        nodes = sa.Table('nodes', self.metadata, autoload=True)
        assign_mapper(self.ctx, Nodes, nodes,
          properties={'nics': sa.relation(Nics, entity_name=self.entity_name)},
          entity_name=self.entity_name)

        packages = sa.Table('packages', self.metadata, autoload=True)
        assign_mapper(self.ctx, Packages, packages,
                      entity_name=self.entity_name)

        partitions = sa.Table('partitions', self.metadata, autoload=True)
        assign_mapper(self.ctx, Partitions, partitions,
                      entity_name=self.entity_name)

        scripts = sa.Table('scripts', self.metadata, autoload=True)
        assign_mapper(self.ctx, Scripts, scripts,
                      entity_name=self.entity_name)

        repos = sa.Table('repos', self.metadata, autoload=True)
        assign_mapper(self.ctx, Repos, repos,
          properties={'nodegroups': sa.relation(NodeGroups,
                                                entity_name=self.entity_name),
                      'kits': sa.relation(Kits, secondary=repos_have_kits,
                                          entity_name=self.entity_name)},
          entity_name=self.entity_name)

    def bootstrap(self):
        """bootstrap the necessary tables and fields"""

        try:
            self.dropTables()
        except Exception: pass

        try:
            self.createTables()
        except Exception: pass

        true = sa.literal(True)
        false = sa.literal(False)


        # Create the nodegroups
        # #R - rack, #N - rank
        installer = NodeGroups(ngname='installer', # VERSION+ARCH
                               nameformat='installer-#RR-#NN',
                               installtype='package', type='installer')
        compute = NodeGroups(ngname='compute', nameformat='compute-#RR-#NN',
                             installtype='package', type='compute')

        kusu_dist = os.environ.get('KUSU_DIST', None)

        if kusu_dist:
            compute.kparams = installer.kparams = Dispatcher.get('kparams', default='')

        # more nodegroups
        imaged = NodeGroups(ngname='compute-imaged', nameformat='host#NNN',
                            installtype='disked', type='compute')
        diskless = NodeGroups(ngname='compute-diskless', nameformat='host#NNN',
                              installtype='diskless', type='compute')
        NodeGroups(ngname='unmanaged', nameformat='device#NNN',
                   installtype='unmanaged', type='other')

        # Create the master installer node
        now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        master_node = Nodes(name='master', state='Installed', lastupdate=now, bootfrom=true)
        installer.nodes.append(master_node)

        # creates the necessary modules for image and diskless nodes
        diskless.modules.append(Modules(loadorder=1,module='uhci-hcd'))
        diskless.modules.append(Modules(loadorder=2,module='ohci-hcd'))
        diskless.modules.append(Modules(loadorder=3,module='ehci-hcd'))
        diskless.modules.append(Modules(loadorder=4,module='jbd'))
        diskless.modules.append(Modules(loadorder=5,module='nfs'))
        diskless.modules.append(Modules(loadorder=6,module='ext3'))
        diskless.modules.append(Modules(loadorder=7,module='tg3'))
        diskless.modules.append(Modules(loadorder=8,module='bnx2'))
        diskless.modules.append(Modules(loadorder=9,module='e1000'))
        diskless.modules.append(Modules(loadorder=10,module='mii'))
        diskless.modules.append(Modules(loadorder=11,module='e100'))
        diskless.modules.append(Modules(loadorder=12,module='lockd'))
        diskless.modules.append(Modules(loadorder=13,module='fscache'))
        diskless.modules.append(Modules(loadorder=14,module='nfs_acl'))
        diskless.modules.append(Modules(loadorder=15,module='sunrpc'))
        diskless.modules.append(Modules(loadorder=16,module='mii'))
        diskless.modules.append(Modules(loadorder=17,module='pcnet32'))
        diskless.modules.append(Modules(loadorder=18,module='forcedeth'))
        diskless.modules.append(Modules(loadorder=19,module='autofs4'))
 
        imaged.modules.append(Modules(loadorder=1,module='uhci-hcd'))
        imaged.modules.append(Modules(loadorder=2,module='ohci-hcd'))
        imaged.modules.append(Modules(loadorder=3,module='ehci-hcd'))
        imaged.modules.append(Modules(loadorder=4,module='jbd'))
        imaged.modules.append(Modules(loadorder=5,module='nfs'))
        imaged.modules.append(Modules(loadorder=6,module='ext3'))
        imaged.modules.append(Modules(loadorder=7,module='bonding'))
        imaged.modules.append(Modules(loadorder=8,module='tg3'))
        imaged.modules.append(Modules(loadorder=9,module='bnx2'))
        imaged.modules.append(Modules(loadorder=10,module='e1000'))
        imaged.modules.append(Modules(loadorder=11,module='scsi_mod'))
        imaged.modules.append(Modules(loadorder=12,module='sd_mod'))
        imaged.modules.append(Modules(loadorder=13,module='libata'))
        imaged.modules.append(Modules(loadorder=14,module='ata_piix'))
        imaged.modules.append(Modules(loadorder=15,module='sata_svw'))
        imaged.modules.append(Modules(loadorder=16,module='sata_nv'))
        imaged.modules.append(Modules(loadorder=17,module='ahci'))
        imaged.modules.append(Modules(loadorder=18,module='mptbase'))
        imaged.modules.append(Modules(loadorder=19,module='mptscsih'))
        imaged.modules.append(Modules(loadorder=20,module='scsi_transport_sas'))
        imaged.modules.append(Modules(loadorder=21,module='scsi_transport_fc'))
        imaged.modules.append(Modules(loadorder=22,module='scsi_transport_spi'))
        imaged.modules.append(Modules(loadorder=23,module='mptsas'))
        imaged.modules.append(Modules(loadorder=24,module='mptfc'))
        imaged.modules.append(Modules(loadorder=25,module='mptspi'))
        imaged.modules.append(Modules(loadorder=26,module='lockd'))
        imaged.modules.append(Modules(loadorder=27,module='fscache'))
        imaged.modules.append(Modules(loadorder=28,module='nfs_acl'))
        imaged.modules.append(Modules(loadorder=29,module='sunrpc'))
        imaged.modules.append(Modules(loadorder=30,module='mii'))
        imaged.modules.append(Modules(loadorder=31,module='e100'))
        imaged.modules.append(Modules(loadorder=32,module='pcnet32'))
        imaged.modules.append(Modules(loadorder=33,module='forcedeth'))
        imaged.modules.append(Modules(loadorder=34,module='autofs4'))

        # Creates the necessary pkg list for image and diskless nodes
        diskless.packages.append(Packages(packagename='SysVinit'))
        diskless.packages.append(Packages(packagename='basesystem'))
        diskless.packages.append(Packages(packagename='bash'))
        if kusu_dist and kusu_dist == 'fedora':
            diskless.packages.append(Packages(packagename='fedora-release'))
        else:
            diskless.packages.append(Packages(packagename='redhat-release'))
        diskless.packages.append(Packages(packagename='chkconfig'))
        diskless.packages.append(Packages(packagename='coreutils'))
        diskless.packages.append(Packages(packagename='db4'))
        diskless.packages.append(Packages(packagename='e2fsprogs'))
        diskless.packages.append(Packages(packagename='filesystem'))
        diskless.packages.append(Packages(packagename='findutils'))
        diskless.packages.append(Packages(packagename='gawk'))
        diskless.packages.append(Packages(packagename='cracklib-dicts'))
        diskless.packages.append(Packages(packagename='glibc'))
        diskless.packages.append(Packages(packagename='glibc-common'))
        diskless.packages.append(Packages(packagename='initscripts'))
        diskless.packages.append(Packages(packagename='iproute'))
        diskless.packages.append(Packages(packagename='iputils'))
        diskless.packages.append(Packages(packagename='krb5-libs'))
        diskless.packages.append(Packages(packagename='libacl'))
        diskless.packages.append(Packages(packagename='libattr'))
        diskless.packages.append(Packages(packagename='libgcc'))
        diskless.packages.append(Packages(packagename='libstdc++'))
        diskless.packages.append(Packages(packagename='libtermcap'))
        diskless.packages.append(Packages(packagename='mingetty'))
        diskless.packages.append(Packages(packagename='mktemp'))
        diskless.packages.append(Packages(packagename='ncurses'))
        diskless.packages.append(Packages(packagename='net-tools'))
        diskless.packages.append(Packages(packagename='nfs-utils'))
        diskless.packages.append(Packages(packagename='pam'))
        diskless.packages.append(Packages(packagename='pcre'))
        diskless.packages.append(Packages(packagename='popt'))
        diskless.packages.append(Packages(packagename='portmap'))
        diskless.packages.append(Packages(packagename='procps'))
        diskless.packages.append(Packages(packagename='psmisc'))
        diskless.packages.append(Packages(packagename='rdate'))
        diskless.packages.append(Packages(packagename='rsh'))
        diskless.packages.append(Packages(packagename='rsh-server'))
        diskless.packages.append(Packages(packagename='rsync'))
        diskless.packages.append(Packages(packagename='sed'))
        diskless.packages.append(Packages(packagename='setup'))
        diskless.packages.append(Packages(packagename='shadow-utils'))
        diskless.packages.append(Packages(packagename='openssh'))
        diskless.packages.append(Packages(packagename='openssh-server'))
        diskless.packages.append(Packages(packagename='openssh-clients'))
        diskless.packages.append(Packages(packagename='sysklogd'))
        diskless.packages.append(Packages(packagename='tcp_wrappers'))
        diskless.packages.append(Packages(packagename='termcap'))
        diskless.packages.append(Packages(packagename='tzdata'))
        diskless.packages.append(Packages(packagename='util-linux'))
        diskless.packages.append(Packages(packagename='words'))
        diskless.packages.append(Packages(packagename='xinetd'))
        diskless.packages.append(Packages(packagename='zlib'))
        diskless.packages.append(Packages(packagename='tar'))
        diskless.packages.append(Packages(packagename='mkinitrd'))
        diskless.packages.append(Packages(packagename='less'))
        diskless.packages.append(Packages(packagename='gzip'))
        diskless.packages.append(Packages(packagename='which'))
        diskless.packages.append(Packages(packagename='util-linux'))
        diskless.packages.append(Packages(packagename='module-init-tools'))
        diskless.packages.append(Packages(packagename='udev'))
        diskless.packages.append(Packages(packagename='cracklib'))
        diskless.packages.append(Packages(packagename='yum'))
        diskless.packages.append(Packages(packagename='vim-minimal'))
        diskless.packages.append(Packages(packagename='vim-common'))
        diskless.packages.append(Packages(packagename='vim-enhanced'))
        diskless.packages.append(Packages(packagename='rootfiles'))
        diskless.packages.append(Packages(packagename='autofs'))
        diskless.packages.append(Packages(packagename='ntp'))

        imaged.packages.append(Packages(packagename='SysVinit'))
        imaged.packages.append(Packages(packagename='basesystem'))
        imaged.packages.append(Packages(packagename='bash'))
        imaged.packages.append(Packages(packagename='kernel'))
        imaged.packages.append(Packages(packagename='grub'))
        if kusu_dist and kusu_dist == 'fedora':
            imaged.packages.append(Packages(packagename='fedora-release'))
        else:
            imaged.packages.append(Packages(packagename='redhat-release'))
        imaged.packages.append(Packages(packagename='chkconfig'))
        imaged.packages.append(Packages(packagename='coreutils'))
        imaged.packages.append(Packages(packagename='db4'))
        imaged.packages.append(Packages(packagename='e2fsprogs'))
        imaged.packages.append(Packages(packagename='filesystem'))
        imaged.packages.append(Packages(packagename='findutils'))
        imaged.packages.append(Packages(packagename='gawk'))
        imaged.packages.append(Packages(packagename='cracklib-dicts'))
        imaged.packages.append(Packages(packagename='glibc'))
        imaged.packages.append(Packages(packagename='glibc-common'))
        imaged.packages.append(Packages(packagename='initscripts'))
        imaged.packages.append(Packages(packagename='iproute'))
        imaged.packages.append(Packages(packagename='iputils'))
        imaged.packages.append(Packages(packagename='krb5-libs'))
        imaged.packages.append(Packages(packagename='libacl'))
        imaged.packages.append(Packages(packagename='libattr'))
        imaged.packages.append(Packages(packagename='libgcc'))
        imaged.packages.append(Packages(packagename='libstdc++'))
        imaged.packages.append(Packages(packagename='libtermcap'))
        imaged.packages.append(Packages(packagename='mingetty'))
        imaged.packages.append(Packages(packagename='mktemp'))
        imaged.packages.append(Packages(packagename='ncurses'))
        imaged.packages.append(Packages(packagename='net-tools'))
        imaged.packages.append(Packages(packagename='nfs-utils'))
        imaged.packages.append(Packages(packagename='pam'))
        imaged.packages.append(Packages(packagename='pcre'))
        imaged.packages.append(Packages(packagename='popt'))
        imaged.packages.append(Packages(packagename='portmap'))
        imaged.packages.append(Packages(packagename='procps'))
        imaged.packages.append(Packages(packagename='psmisc'))
        imaged.packages.append(Packages(packagename='rdate'))
        imaged.packages.append(Packages(packagename='rsh'))
        imaged.packages.append(Packages(packagename='rsh-server'))
        imaged.packages.append(Packages(packagename='rsync'))
        imaged.packages.append(Packages(packagename='sed'))
        imaged.packages.append(Packages(packagename='setup'))
        imaged.packages.append(Packages(packagename='shadow-utils'))
        imaged.packages.append(Packages(packagename='openssh'))
        imaged.packages.append(Packages(packagename='openssh-server'))
        imaged.packages.append(Packages(packagename='openssh-clients'))
        imaged.packages.append(Packages(packagename='sysklogd'))
        imaged.packages.append(Packages(packagename='tcp_wrappers'))
        imaged.packages.append(Packages(packagename='termcap'))
        imaged.packages.append(Packages(packagename='tzdata'))
        imaged.packages.append(Packages(packagename='util-linux'))
        imaged.packages.append(Packages(packagename='words'))
        imaged.packages.append(Packages(packagename='xinetd'))
        imaged.packages.append(Packages(packagename='zlib'))
        imaged.packages.append(Packages(packagename='tar'))
        imaged.packages.append(Packages(packagename='mkinitrd'))
        imaged.packages.append(Packages(packagename='less'))
        imaged.packages.append(Packages(packagename='gzip'))
        imaged.packages.append(Packages(packagename='which'))
        imaged.packages.append(Packages(packagename='util-linux'))
        imaged.packages.append(Packages(packagename='module-init-tools'))
        imaged.packages.append(Packages(packagename='udev'))
        imaged.packages.append(Packages(packagename='cracklib'))
        imaged.packages.append(Packages(packagename='yum'))
        imaged.packages.append(Packages(packagename='vim-minimal'))
        imaged.packages.append(Packages(packagename='vim-common'))
        imaged.packages.append(Packages(packagename='vim-enhanced'))
        imaged.packages.append(Packages(packagename='rootfiles'))
        imaged.packages.append(Packages(packagename='autofs'))
        imaged.packages.append(Packages(packagename='ntp'))

        # Create the partition entries for the compute node
        # REGULAR PARTITIONING

        # use literals so we can overcome mysql and postgres specifics

        for ng in [compute]:
            boot = Partitions(mntpnt='/boot', fstype='ext3', partition='1',
                              size='100', device='1', preserve=false)
            root = Partitions(mntpnt='/', fstype='ext3', partition='2',
                              size='12000', device='1', preserve=false)
            swap = Partitions(fstype='linux-swap', partition='3',
                              size='2000', device='1', preserve=false)
            var = Partitions(mntpnt='/var', fstype='ext3', partition='5',
                             size='2000', device='1', preserve=false)
            data = Partitions(mntpnt='/data', fstype='ext3', partition='6', size='14000',
                              options='fill', device='1', preserve=false)
            dell = Partitions(options='partitionID=Dell Utility', preserve=true)
            donotpreserve = Partitions(options='partitionID=*', preserve=false)
            ng.partitions.append(boot)
            ng.partitions.append(root)
            ng.partitions.append(swap)
            ng.partitions.append(var)
            ng.partitions.append(data)
            ng.partitions.append(dell)
            ng.partitions.append(donotpreserve)
# LVM PARTITIONING
#        for ng in [compute]:
#            boot = Partitions(mntpnt='/boot', fstype='ext3', partition='1',
#                              size='100', device='1', preserve=false)
#            swap = Partitions(fstype='linux-swap', partition='2',
#                              size='2000', device='1', preserve=false)
#            pv = Partitions(fstype='physical volume', partition='0',
#                            size='28000', device='N', preserve=false,
#                            options='fill;pv;vg=VolGroup00')
#            vg = Partitions(device='VolGroup00', options='vg;extent=32M', preserve=false)
#            root = Partitions(mntpnt='/', fstype='ext3', size='12000',
#                              device='ROOT', options='lv;vg=VolGroup00', preserve=false)
#            var = Partitions(mntpnt='/var', fstype='ext3', size='2000',
#                             device='VAR', options='lv;vg=VolGroup00', preserve=false)
#            data = Partitions(mntpnt='/data', fstype='ext3', size='14000',
#                              device='DATA', options='lv;vg=VolGroup00;fill', preserve=false)
#            dell = Partitions(options='partitionID=Dell Utility', preserve=true)
##            donotpreserve1 = Partitions(options='partitionID=Linux', preserve=false)
##            donotpreserve2 = Partitions(options='partitionID=Linux swap', preserve=false)
##            donotpreserve3 = Partitions(options='partitionID=Linux extended', preserve=false)
#            donotpreserve4 = Partitions(options='partitionID=*', preserve=false)

#            ng.partitions.append(boot)
#            ng.partitions.append(swap)
#            ng.partitions.append(pv)
#            ng.partitions.append(vg)
#            ng.partitions.append(root)
#            ng.partitions.append(var)
#            ng.partitions.append(data)
#            ng.partitions.append(dell)
##            ng.partitions.append(donotpreserve1)
##            ng.partitions.append(donotpreserve2)
##            ng.partitions.append(donotpreserve3)
#            ng.partitions.append(donotpreserve4)
        # Imaged Partitioning
        boot = Partitions(mntpnt='/boot', fstype='ext2', partition='1',
                          size='100', device='1', preserve=false)
        swap = Partitions(fstype='linux-swap', partition='2',
                          size='8000', device='1', preserve=false)
        root = Partitions(mntpnt='/', fstype='ext3', partition='3',
                          size='24000', device='1', preserve=false)
        imaged.partitions.append(boot)
        imaged.partitions.append(swap)
        imaged.partitions.append(root)

        # Installer Partitioning Schema
        boot = Partitions(mntpnt='/boot', fstype='ext3', partition='1',
                          size='100', device='1', preserve=false)
        swap = Partitions(fstype='linux-swap', partition='2',
                          size='2000', device='1', preserve=false)
        pv = Partitions(fstype='physical volume', partition='0',
                        size='28000', device='N', preserve=false,
                        options='fill;pv;vg=KusuVolGroup00')
        vg = Partitions(device='KusuVolGroup00', options='vg;extent=32M', preserve=false)
        root = Partitions(mntpnt='/', fstype='ext3', size='12000',
                          device='ROOT', options='lv;vg=KusuVolGroup00', preserve=false)
        depot = Partitions(mntpnt='/depot', fstype='ext3', size='10000',
                           device='DEPOT', options='lv;vg=KusuVolGroup00', preserve=false)
        var = Partitions(mntpnt='/var', fstype='ext3', size='2000',
                         device='VAR', options='lv;vg=KusuVolGroup00', preserve=false)
        dell = Partitions(options='partitionID=Dell Utility', preserve=true)
        donotpreserve = Partitions(options='partitionID=*', preserve=false)
        for parts in [boot, swap, pv, vg, root, depot, var, dell, donotpreserve]:
            installer.partitions.append(parts)
        # End Installer Partitioning Schema

        # default appglobals values
        AppGlobals(kname='CFMBaseDir', kvalue='/opt/kusu/cfm')
        AppGlobals(kname='InstallerServeDNS', kvalue='1')
        AppGlobals(kname='InstallerServeNIS', kvalue='0')
        AppGlobals(kname='InstallerServeNTP', kvalue='1')
        AppGlobals(kname='InstallerServeNFS', kvalue='1')
#        AppGlobals(kname='ImageBaseDir', kvalue='/depot/images')
        AppGlobals(kname='DEPOT_KITS_ROOT', kvalue='/depot/kits')
        AppGlobals(kname='DEPOT_IMAGES_ROOT', kvalue='/depot/images')
        AppGlobals(kname='DEPOT_REPOS_ROOT', kvalue='/depot/repos')
        AppGlobals(kname='DEPOT_REPOS_SCRIPTS', kvalue='/depot/repos/custom_scripts/')
        AppGlobals(kname='DEPOT_REPOS_POST', kvalue='/depot/repos/post_scripts')
        AppGlobals(kname='DEPOT_CONTRIB_ROOT', kvalue='/depot/contrib')
        AppGlobals(kname='DEPOT_UPDATES_ROOT', kvalue='/depot/updates')
        AppGlobals(kname='DEPOT_AUTOINST_ROOT', kvalue='/depot/repos/instconf')
        AppGlobals(kname='PIXIE_ROOT', kvalue='/tftpboot/kusu')
        AppGlobals(kname='PROVISION', kvalue='KUSU')
        AppGlobals(kname='KUSU_VERSION', kvalue='1.2')
        Repos(repoid=999, reponame="DELETEME")
        self.flush()
        if self.driver =='postgres':
            self.postgres_update_sequences(self.postgres_get_seq_list())

    def createDatabase(self):
        """Creates the database"""

        if self.driver == 'mysql':
            try:
                if self.password:
                    cmd = 'mysql -u %s -p%s -h %s -P %s -e "create database %s;"' % \
                          (self.username, self.password, self.host, self.port, self.db)
                else:
                    cmd = 'mysql -u %s -h %s -P %s -e "create database %s;"' % \
                          (self.username, self.host, self.port, self.db)

                p = subprocess.Popen(cmd,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                out, err = p.communicate()
                retcode = p.returncode
            except:
                raise CommandFailedToRunError
        elif self.driver == 'postgres':
            try:
                # ignore self.password for now
                # expect to have a psql create role apache with superuser login to be run
                # already.
                cmd = 'psql -p %s  postgres %s   -c "create database %s with owner = %s;"'\
                      % (self.port, self.username, self.db, self.username)
                p = subprocess.Popen(cmd,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                out, err = p.communicate()
                retcode = p.returncode
            except:
                raise CommandFailedToRunError
            if retcode:
                raise FailedToCreateDatabase, 'Unable to create database: %s' % self.db
        else:
            raise NotSupportedDatabaseCreationError, 'Database creation not supported for %s' % self.driver

    def dropDatabase(self):
        """Drops the database"""

        if self.driver == 'mysql':
            try:
                if self.password:
                    cmd = 'mysql -u %s -p%s -h %s -P %s -e "drop database %s;"' % \
                          (self.username, self.password, self.host, self.port, self.db)
                else:
                    cmd = 'mysql -u %s -h %s -P %s -e "drop database %s;"' % \
                          (self.username, self.host, self.port, self.db)

                p = subprocess.Popen(cmd,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                out, err = p.communicate()
                retcode = p.returncode
            except:
                raise CommandFailedToRunError
            if retcode:
                raise FailedToDropDatabase, 'Unable to drop database: %s' % self.db
        elif self.driver == 'postgres':
            try:
                # disconnect from the database
                # ignore self.password for now
                self.flush()
                cmd = 'psql -p %s postgres   %s  -c "drop database %s;'\
                      % (self.port,self.username, self.db)
                p = subprocess.Popen(cmd,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                out, err = p.communicate()
                retcode = p.returncode
            except:
                    raise CommandFailedToRunError

            if retcode:
                raise FailedToDropDatabase, 'Unable to drop database: %s' % self.db

        else:
            raise NotSupportedDatabaseCreationError, 'Database creation not supported for %s' % self.driver

    def destroy(self):
        pass

    def createSession(self):
        """Returns a sqlalchemy session"""

        return sa.create_session()

    def flush(self):
        """Flushes the current session context."""

        self.ctx.current.flush()
        self.ctx.current.clear()

    def copyTo(self, other_db):
        """Copies the content of current database to
           a new database. Existing tables and data on
           the new database will be deleted.
        """

        if not isinstance(other_db, DB):
            raise TypeError, "Class '%s' is not a DB class" % other_db.__class__.__name__

        if other_db.driver == 'mysql':
            try:
                other_db.dropDatabase()
            except: pass
        if other_db.driver == 'postgres':
            try:
                other_db.dropDatabase()
            except:
                pass
        other_db.createDatabase()

        other_db.dropTables()

        # Creates the tables
        other_db.createTables()

        # Copy them in order to preserve relationship
        # Order by primary, secondary(1-M) and 
        # junction tables(M-N)
        for table in ['AppGlobals', 'Repos', 'OS', 'Kits', 'Networks', \
                      'Components', 'NodeGroups', 'Modules', \
                      'Nodes', 'Packages', 'Partitions', 'Scripts', 'DriverPacks', \
                      'Nics', 'NGHasComp', 'ReposHaveKits', 'NGHasNet']:
            for obj in getattr(self, table).select():
                try:
                    #obj.expunge(entity_name=self.entity_name)
                    obj.expunge()
                except: pass

                # Fully detatch the object
                if hasattr(obj, '_instance_key'):
                    delattr(obj, '_instance_key')
                #try:
                obj.save_or_update(entity_name=other_db.entity_name)
                obj.flush()
                #except Exception ,e :
                    #raise UnableToSaveDataError, obj
            if other_db.driver =='postgres':
                other_db.postgres_update_sequences(other_db.postgres_get_seq_list())

    def postgres_exec_raw_stmt(self,str):
        """Postgres raw statements execution function
        Returns a list of lists, with each list representing a row"""
        if self.metadata.engine.name != 'postgres':
            return None
        res = self.metadata.engine.execute(str)
        if res.rowcount > 0: # -1 for grant etc..
            return [ list(name) for name in res]
        else:
            return []

    def postgres_get_table_list(self):
        sql = "select table_name from information_schema.tables"\
        " where table_schema='public';"
        res = self.postgres_exec_raw_stmt(sql)
        if res:
            return [ tupl[0] for tupl in res]
        else:
            return None

    def postgres_get_seq_list(self):
        sql = "SELECT relname FROM pg_class WHERE relkind = 'S'"\
            " AND relnamespace IN ( SELECT oid FROM pg_namespace" \
            " WHERE  nspname = 'public')"
        res = self.postgres_exec_raw_stmt(sql)
        if res:
            return [ tupl[0] for tupl in res]
        else:
            return None # programatically, there can be no sequences.

    def postgres_update_sequences(self,seq):
        tbl_column_pairs = [  tuple(l.split('_')[:2])   for l in seq ]
        for t,c in tbl_column_pairs :
            sql =  "SELECT setval('%s_%s_seq', (SELECT MAX(%s) from %s))" %\
              ( t , c , c , t)
            res = self.postgres_exec_raw_stmt(sql)
            # We are flushing once per object. Flushing the entire database
            # causes an exception to be raised, as described in KUSU-507.
#             try:
#                other_db.flush()
#             except sa.exceptions, e: 
#                raise UnableToCommitDataError, e
#             except Exception, e:
#                raise KusuError, e

def findNodeGroupsFromKit(db, columns=[], ngargs={}, kitargs={}):
    """
    Selects nodegroups to which a specified kit is assigned:
    SELECT cols FROM nodegroups WHERE ng <-> ng_has_comp <-> components <-> kits

    columns -- a list of nodegroups columns to select; set to [] to select all.
    ngargs -- a dictionary of nodegroups columns to match in WHERE clause
    kitargs -- a dictionary of kits columns to match in WHERE clause
    """

    if not columns:
        stmt = db.nodegroups.select()
    else:
        stmt = sa.select([getattr(db.nodegroups.c, col) for col in columns])

    stmt.distinct = True
    stmt.append_from(
        db.nodegroups.join(db.ng_has_comp,
                           db.nodegroups.c.ngid == db.ng_has_comp.c.ngid).join(
                           db.components,
                           db.ng_has_comp.c.cid == db.components.c.cid).join(
                           db.kits, db.components.c.kid == db.kits.c.kid))

    for arg in ngargs:
        if db.nodegroups.c.has_key(arg) and ngargs[arg] is not None:
            stmt.append_whereclause(getattr(db.nodegroups.c, arg) == \
                                    ngargs[arg])
        elif not db.nodegroups.c.has_key(arg):
            raise NoSuchColumnError, \
                "Invalid column '%s' for table '%s'" % (arg, db.nodegroups.name)

    for arg in kitargs:
        if db.kits.c.has_key(arg) and kitargs[arg] is not None:
            stmt.append_whereclause(getattr(db.kits.c, arg) == kitargs[arg])
        elif not db.kits.c.has_key(arg):
            raise NoSuchColumnError, \
                "Invalid column '%s' for table '%s'" % (arg, db.kits.name)

    return stmt.execute().fetchall()

def findKitsFromNodeGroup(db, columns=[], kitargs={}, ngargs={}):
    """
    Selects kits which belong the a specific nodegroup
    SELECT cols FROM kits
    WHERE kits <-> components <-> ng_has_comp <-> nodegroups

    columns -- a list of kits columns to select; set to [] to select all.
    kitargs -- a dictionary of kits columns to match in WHERE clause
    ngargs -- a dictionary of nodegroups columns to match in WHERE clause
    """

    if not columns:
        stmt = db.kits.select()
    else:
        stmt = sa.select([getattr(db.kits.c, col) for col in columns])

    stmt.distinct = True
    stmt.append_from(
        db.kits.join(db.components, db.kits.c.kid == db.components.c.kid).join(
                     db.ng_has_comp,
                     db.components.c.cid == db.ng_has_comp.c.cid).join(
                     db.nodegroups,
                     db.ng_has_comp.c.ngid == db.nodegroups.c.ngid))

    for arg in ngargs:
        if db.nodegroups.c.has_key(arg) and ngargs[arg] is not None:
            stmt.append_whereclause(getattr(db.nodegroups.c, arg) == \
                                    ngargs[arg])
        elif not db.nodegroups.c.has_key(arg):
            raise NoSuchColumnError, \
                "Invalid column '%s' for table '%s'" % (arg, db.nodegroups.name)

    for arg in kitargs:
        if db.kits.c.has_key(arg) and kitargs[arg] is not None:
            stmt.append_whereclause(getattr(db.kits.c, arg) == kitargs[arg])
        elif not db.kits.c.has_key(arg):
            raise NoSuchColumnError, \
                "Invalid column '%s' for table '%s'" % (arg, db.kits.name)

    return stmt.execute().fetchall()
