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
logging.getLogger('sqlalchemy').parent = kusulog.getKusuLog()

# it seems these must be told to be quiet individually...
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm.attributes').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm.attributes.InstrumentedAttribute').           setLevel(logging.WARNING)
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
    cols = ['kid', 'cname', 'cdesc', 'os']
    def __repr__(self):
        return '%s(%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.kid, self.cname, self.os,
                self.cdesc)

class Kits(BaseTable): 
    cols = ['rname', 'rdesc', 'version', \
            'isOS', 'removable', 'arch']

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

    def getPath(self):
        return '/depot/kits/%s%s%s' % self.prepNameVerArch('/')

    longname = property(getLongName)
    path = property(getPath)

    def __repr__(self):
        return '%s(%r,%r,%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.rname, self.version, self.arch,
               self.rdesc, self.isOS, self.removable)

class Modules(BaseTable): 
    cols = ['ngid', 'module', 'loadorder']
    def __repr__(self):
        return '%s(%r,%r,%r)' % \
               (self.__class__.__name__, self.ngid, self.module, self.loadorder)

class Networks(BaseTable): 
    cols = ['network', 'subnet', 'device', 'suffix', \
            'gateway', 'options', 'netname', 'startip', \
            'inc', 'usingdhcp']
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

class DB(object):

    tableClasses = {'ReposHaveKits' : ReposHaveKits,
                    'AppGlobals' : AppGlobals,
                    'Components' : Components,
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
                    'Repos' : Repos}

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
 
        #elif driver == 'postgres':
        #    if not port:
        #        port = '5432'
        #
        #    self.engine_src = 'postgres://%s:%s@%s:%s/%s' % \
        #                      (username, password, host, port, db)

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
            sa.Column('kname', sa.String(20), unique=True),
            sa.Column('kvalue', sa.String(255)),
            sa.Column('ngid', sa.Integer),
            mysql_engine='InnoDB')

        components = sa.Table('components', self.metadata,
            sa.Column('cid', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('kid', sa.Integer, sa.ForeignKey('kits.kid'), nullable=False),
            sa.Column('cname', sa.String(255)),
            sa.Column('cdesc', sa.String(255)),
            sa.Column('os', sa.String(20)),
            mysql_engine='InnoDB')
        sa.Index('components_FKIndex1', components.c.kid)

        kits = sa.Table('kits', self.metadata,
            sa.Column('kid', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('rname', sa.String(45)),
            sa.Column('rdesc', sa.String(255)),
            sa.Column('version', sa.String(20)),
            sa.Column('isOS', sa.Boolean, sa.PassiveDefault('0')),
            sa.Column('removeable', sa.Boolean, sa.PassiveDefault('0')),
            sa.Column('arch', sa.String(20)),
            mysql_engine='InnoDB')

        modules = sa.Table('modules', self.metadata,
            sa.Column('mid', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('ngid', sa.Integer, primary_key=True),
            sa.Column('module', sa.String(45)),
            sa.Column('loadorder', sa.Integer, sa.PassiveDefault('0')),
            sa.ForeignKeyConstraint(['ngid'], 
                                    ['nodegroups.ngid']),
            mysql_engine='InnoDB')
        sa.Index('modules_FKIndex1', modules.c.ngid)

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
            sa.Column('usingdhcp', sa.Boolean, sa.PassiveDefault('0')),
            mysql_engine='InnoDB')

        ng_has_comp = sa.Table('ng_has_comp', self.metadata,
            sa.Column('ngid', sa.Integer, primary_key=True, nullable=False),
            sa.Column('cid', sa.Integer, primary_key=True, nullable=False),
            sa.ForeignKeyConstraint(['ngid'], ['nodegroups.ngid']),
            sa.ForeignKeyConstraint(['cid'], ['components.cid']),
            mysql_engine='InnoDB')
        sa.Index('comp2ng_FKIndex1', ng_has_comp.c.cid)
        sa.Index('comp2ng_FKIndex2', ng_has_comp.c.ngid)
       
        # Again, this is a M-N table. 
        ng_has_net = sa.Table('ng_has_net', self.metadata,
            sa.Column('ngid', sa.Integer, primary_key=True, nullable=False),
            sa.Column('netid', sa.Integer, primary_key=True, nullable=False),
            sa.ForeignKeyConstraint(['ngid'], ['nodegroups.ngid']),
            sa.ForeignKeyConstraint(['netid'], ['networks.netid']),
            mysql_engine='InnoDB')
        sa.Index('net2ng_FKIndex1', ng_has_net.c.netid)
        sa.Index('net2ng_FKIndex2', ng_has_net.c.ngid)

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
            sa.Column('mac', sa.String(45)),
            sa.Column('ip', sa.String(20)),
            sa.Column('boot', sa.Boolean, sa.PassiveDefault('0')),
            mysql_engine='InnoDB')
        sa.Index('nics_FKIndex1', nics.c.nid)
        sa.Index('nics_FKIndex2', nics.c.netid)

        # If repoid is not nullable(nullable=False), a repo 
        # has to be created (at least inserted into the table) 
        # first before a nodegroup entry is made
        #
        # How can a repo be created when the 
        # ng_has_comp is not filled up, which needs
        # a nodegroup first? Without ng_has_comp, 
        # no references can be made to components, then 
        # to kits, which a repo is made out of.
        #
        # Therefore, it has been changed to nullable=True
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

        partitions = sa.Table('partitions', self.metadata,
            sa.Column('idpartitions', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('ngid', sa.Integer, nullable=False),
            sa.Column('device', sa.String(255)),
            sa.Column('partition', sa.String(255)),
            sa.Column('mntpnt', sa.String(255)),
            sa.Column('fstype', sa.String(20)),
            sa.Column('size', sa.String(45)),
            sa.Column('options', sa.String(255)),
            sa.Column('preserve', sa.Boolean),
            sa.ForeignKeyConstraint(['ngid'],
                                    ['nodegroups.ngid']),
            mysql_engine='InnoDB')
        sa.Index('partitions_FKIndex1', partitions.c.ngid)

        repos = sa.Table('repos', self.metadata,
            sa.Column('repoid', sa.Integer, primary_key=True,
                      autoincrement=True),
            sa.Column('reponame', sa.String(45)),
            sa.Column('repository', sa.String(255)),
            sa.Column('installers', sa.String(255)),
            sa.Column('ostype', sa.String(20)),
            mysql_engine='InnoDB')

        # A junction table. M-N relationship
        repos_have_kits = sa.Table('repos_have_kits', self.metadata,
            sa.Column('repoid', sa.Integer, primary_key=True),
            sa.Column('kid', sa.Integer, primary_key=True),
            sa.ForeignKeyConstraint(['repoid'], ['repos.repoid']),
            sa.ForeignKeyConstraint(['kid'], ['kits.kid']),
            mysql_engine='InnoDB')
        sa.Index('repos_has_rolls_FKIndex1', repos_have_kits.c.repoid)
        sa.Index('repos_has_kits_FKIndex2', repos_have_kits.c.kid)

        scripts = sa.Table('scripts', self.metadata,
            sa.Column('idscripts', sa.Integer, primary_key=True),
            sa.Column('ngid', sa.Integer, primary_key=True),
            sa.Column('script', sa.String(255)),
            sa.ForeignKeyConstraint(['ngid'],
                                    ['nodegroups.ngid']),
            mysql_engine='InnoDB')
        sa.Index('scripts_FKIndex1', scripts.c.ngid)

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
                                         entity_name=self.entity_name)},
          entity_name=self.entity_name)

        kits = sa.Table('kits', self.metadata, autoload=True)
        assign_mapper(self.ctx, Kits, kits,
          properties={'components': sa.relation(Components,
                                                entity_name=self.entity_name),
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
            self.createTables()
        except Exception: pass

        # Create the nodegroups
        # #R - rack, #N - rank
        master = NodeGroups(ngname='master', nameformat='master-#N',
                            installtype='package', type='installer')
        installer = NodeGroups(ngname='installer', # VERSION+ARCH
                               nameformat='installer-#RR-#NN',
                               installtype='package', type='installer')
        compute = NodeGroups(ngname='compute', nameformat='compute-#RR-#NN',
                             installtype='package', type='compute')

        kusu_dist = os.environ.get('KUSU_DIST', None)

        if kusu_dist and kusu_dist in ['fedora', 'centos', 'rhel']:
            master.kparamas = 'text noipv6 kssendmac'
            installer.kparams = 'text noipv6 kssendmac'
            compute.kparams = 'text noipv6 kssendmac'
            
        # more nodegroups
        NodeGroups(ngname='compute-disked', nameformat='c#RR-#NN',
                   installtype='disked', type='compute')
        NodeGroups(ngname='compute-diskless', nameformat='host#NNN',
                   installtype='diskless', type='compute')
        NodeGroups(ngname='unmanaged', nameformat='c#RR-#NN',
                   installtype='unmanaged', type='other')

        # Create the master installer node
        now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        master_node = Nodes(name='master-0', state='installed', lastupdate=now)
        master.nodes.append(master_node)

        # Create the partition entries for the compute node
# REGULAR PARTITIONING
#        boot = Partitions(mntpnt='/boot', fstype='ext3', partition='1',
#                          size='100', device='1', preserve='N')
#        root = Partitions(mntpnt='/', fstype='ext3', partition='2',
#                          size='4000', device='1', preserve='N')
#        swap = Partitions(partition='3', fstype='linux-swap',
#                          size='2000', device='1', preserve='N')
#        data = Partitions(mntpnt='/data', fstype='ext3', partition='4', size='4000',
#                          options='fill', device='1', preserve='N')
#        compute.partitions.append(boot)
#        compute.partitions.append(root)
#        compute.partitions.append(swap)
#        compute.partitions.append(data)
# LVM PARTITIONING
        boot = Partitions(mntpnt='/boot', fstype='ext3', partition='1',
                          size='100', device='1', preserve='N')
        swap = Partitions(fstype='linux-swap', partition='2',
                          size='2000', device='1', preserve='N')
        pv = Partitions(fstype='physical volume', partition='N',
                        size='6000', device='N', preserve='N',
                        options='fill;pv;vg=VolGroup00')
        vg = Partitions(device='VolGroup00', options='vg;extent=32M')
        root = Partitions(mntpnt='/', fstype='ext3', size='2000',
                          device='ROOT', options='lv;vg=VolGroup00')
        data = Partitions(mntpnt='/data', fstype='ext3', size='4000',
                          device='DATA', options='lv;vg=VolGroup00;fill')
        compute.partitions.append(boot)
        compute.partitions.append(swap)
        compute.partitions.append(pv)
        compute.partitions.append(vg)
        compute.partitions.append(root)
        compute.partitions.append(data)

        # default appglobals values
        AppGlobals(kname='CFMBaseDir', kvalue='/opt/kusu/cfm')
        AppGlobals(kname='InstallerServeDNS', kvalue='1')
        AppGlobals(kname='InstallerServeNIS', kvalue='0')
        AppGlobals(kname='InstallerServeNTP', kvalue='0')
        AppGlobals(kname='InstallerServeNFS', kvalue='0')
        AppGlobals(kname='ImageBaseDir', kvalue='/depot/images')

        Repos(repoid=999, reponame="DELETEME")
        self.flush()

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

            other_db.createDatabase()

        other_db.dropTables()

        # Creates the tables
        other_db.createTables()

        # Copy them in order to preserve relationship
        # Order by primary, secondary(1-M) and 
        # junction tables(M-N)
        for table in ['AppGlobals', 'Repos', 'Kits', 'Networks', \
                      'Components', 'NodeGroups', 'Modules', \
                      'Nodes', 'Packages', 'Partitions', 'Scripts', \
                      'Nics', 'NGHasComp', 'ReposHaveKits', 'NGHasNet']:
            for obj in getattr(self, table).select():
                try:
                    obj.expunge(entity_name=self.entity_name)
                except: pass

                # Fully detatch the object
                if hasattr(obj, '_instance_key'):
                    delattr(obj, '_instance_key')

                try:
                    obj.save_or_update(entity_name=other_db.entity_name)
                except:
                    raise UnableToSaveDataError, obj

            try:
                other_db.flush()
            except sa.exceptions, e: 
                raise UnableToCommitDataError, e
            except Exception, e:
                raise KusuError, e
