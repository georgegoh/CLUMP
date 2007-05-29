#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

import sqlalchemy as sa
import os
from kusu.util.errors import *
import kusu.util.log as kusulog
import logging

try:
    import subprocess
except:
    from popen5 import subprocess

logging.getLogger('sqlalchemy').parent = kusulog.getKusuLog()

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
        return '%s(%r,%r,%r)' % \
               (self.__class__.__name__, self.kid, self.cname, self.os)

class Kits(BaseTable): 
    cols = ['rname', 'rdesc', 'version', \
            'isOS', 'removable', 'arch']
    def __repr__(self):
        return '%s(%r,%r,%r)' % \
               (self.__class__.__name__, self.rname, self.version, self.arch)

class Modules(BaseTable): 
    cols = ['ngid', 'module', 'loadorder']

class Networks(BaseTable): 
    cols = ['network', 'subnet', 'device', 'suffix', \
            'gateway', 'options', 'netname', 'startip', \
            'inc', 'usingdhcp']

class NGHasComp(BaseTable):
    cols = ['ngid', 'cid']
    def __repr__(self):
        return '%s(%r,%r)' % \
               (self.__class__.__name__, self.ngid, self.cid)

class NGHasNet(BaseTable):
    cols = ['ngid', 'netid']

class Nics(BaseTable):
    cols = ['nid', 'netid', 'mac', 'ip', 'boot']

class NodeGroups(BaseTable):
    cols = ['repoid', 'ngname', 'installtype', \
            'ngdesc', 'nameformat', 'kernel', 'initrd', \
            'kparams']
    def __repr__(self):
        return '%s(%r,%r)' % \
               (self.__class__.__name__, self.ngname, self.repoid)

class Nodes(BaseTable):
    cols = ['ngid', 'name', 'kernel', 'initrd', \
            'kparams', 'state', 'bootfrom', 'lastupdate', \
            'rack', 'rank']
    def __repr__(self):
        return '%s(%r,%r)' % \
               (self.__class__.__name__, self.ngid, self.name)

class Packages(BaseTable):
    cols = ['ngid', 'packaagename']

class Partitions(BaseTable):
    cols = ['ngid', 'partition', 'mntpnt', 'fstype', \
            'size', 'options', 'preserve']

class Repos(BaseTable):
    cols = ['reponame', 'repository', 'installers', \
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


class DB:

    mapTableClass = { 'repos_have_kits' : ReposHaveKits,
                      'appglobals' : AppGlobals,
                      'components' : Components,
                      'kits' : Kits,
                      'modules' : Modules,
                      'ng_has_comp' : NGHasComp,
                      'networks' : Networks,
                      'nics' : Nics,
                      'ng_has_net' : NGHasNet,
                      'nodegroups' : NodeGroups,              
                      'nodes' : Nodes,
                      'packages' : Packages, 
                      'partitions' : Partitions,
                      'scripts' : Scripts,
                      'repos' : Repos}


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
        
        self.metadata = sa.BoundMetaData(engine_src, \
                                         poolclass=sa.pool.SingletonThreadPool)
        self._defineTables()

    def __getPasswd(self):
        """
        Open self.__passfile to retrieve password, return None on fail.
        """

        try:
            fp = file(self.__passfile, 'r')
        except IOError, msg:
            print "KusuDB: insufficient privileges to access password file"
            print "optionally, the password file may be missing"
            print msg
            return None
        except:
            print "KusuDB: error accessing the password file"
            return None

        cipher = fp.readline().strip()
        fp.close()
        return self.__decrypt(cipher)

    def  __decrypt(self, cipher):
        #convert cipher to decrypted text
        return cipher

    def __encrypt(self):
        pass

    def __getattr__(self, name):
        try:
            # Returns mapper based on class name and entity name
            return sa.orm.class_mapper(self.mapTableClass[name], self.entity_name)
        except:
            raise AttributeError, 'No mapper for table %s' % name

    def _load(self):
        """Loads all table mappers into class attributes. 
           Mapper names are named after table names.
        """

        dtable = {}
        dmapper = {}

        from sqlalchemy.orm.mapper import ClassKey 
 
        if not sa.orm.mapper_registry.has_key(ClassKey(ReposHaveKits, self.entity_name)):
            dtable['repos_have_kits'] = sa.Table('repos_have_kits', self.metadata, autoload=True)
            dmapper['repos_have_kits'] = sa.mapper(ReposHaveKits, dtable['repos_have_kits'], \
                                                   entity_name=self.entity_name)

        if not sa.orm.mapper_registry.has_key(ClassKey(AppGlobals, self.entity_name)):
            dtable['appglobals'] = sa.Table('appglobals', self.metadata, autoload=True)
            dmapper['appglobals'] = sa.mapper(AppGlobals, dtable['appglobals'], entity_name=self.entity_name)

        if not sa.orm.mapper_registry.has_key(ClassKey(NGHasComp, self.entity_name)):
            dtable['ng_has_comp'] = sa.Table('ng_has_comp', self.metadata, autoload=True)
            dmapper['ng_has_comp'] = \
                    sa.mapper(NGHasComp, dtable['ng_has_comp'], entity_name=self.entity_name)
              
        if not sa.orm.mapper_registry.has_key(ClassKey(Components, self.entity_name)):
            dtable['components'] = sa.Table('components', self.metadata, autoload=True)
            dmapper['components'] = sa.mapper(Components, dtable['components'], entity_name=self.entity_name, \
                                        properties={'nodegroups': sa.relation(NodeGroups, secondary=dtable['ng_has_comp'],
                                                                              entity_name=self.entity_name)})

        if not sa.orm.mapper_registry.has_key(ClassKey(Kits, self.entity_name)):
            dtable['kits'] = sa.Table('kits', self.metadata, autoload=True)
            dmapper['kits'] = sa.mapper(Kits, dtable['kits'], \
                                        properties={'components': sa.relation(Components, entity_name=self.entity_name), \
                                                    'repos': sa.relation(Repos, secondary=dtable['repos_have_kits'], \
                                                                         entity_name=self.entity_name), \
                                                    'removable' : dtable['kits'].c.removeable}, \
                                        entity_name=self.entity_name)

        if not sa.orm.mapper_registry.has_key(ClassKey(Modules, self.entity_name)):
            dmapper['modules'] = \
                    sa.mapper(Modules, sa.Table('modules', self.metadata, autoload=True), entity_name=self.entity_name)

        if not sa.orm.mapper_registry.has_key(ClassKey(Networks, self.entity_name)):
            dmapper['networks'] = \
                    sa.mapper(Networks, sa.Table('networks', self.metadata, autoload=True), entity_name=self.entity_name)

        if not sa.orm.mapper_registry.has_key(ClassKey(Nics, self.entity_name)):
            dmapper['nics'] = \
                    sa.mapper(Nics, sa.Table('nics', self.metadata, autoload=True), entity_name=self.entity_name)

        if not sa.orm.mapper_registry.has_key(ClassKey(NGHasNet, self.entity_name)):
            dmapper['ng_has_net'] = \
                    sa.mapper(NGHasNet, sa.Table('ng_has_net', self.metadata, autoload=True), entity_name=self.entity_name)

        if not sa.orm.mapper_registry.has_key(ClassKey(NodeGroups, self.entity_name)):
            dmapper['nodegroups'] = \
                    sa.mapper(NodeGroups, sa.Table('nodegroups', self.metadata, autoload=True), entity_name=self.entity_name, \
                              properties={'components': sa.relation(Components, secondary=dtable['ng_has_comp'],
                                                                    entity_name=self.entity_name)})
                              # Currently nodegroups <-> components relationship is defined twice.
                              # Possible to replace this with ingenious backref-fu.


        if not sa.orm.mapper_registry.has_key(ClassKey(Nodes, self.entity_name)):
            dmapper['nodes'] = \
                    sa.mapper(Nodes, sa.Table('nodes', self.metadata, autoload=True), entity_name=self.entity_name)

        if not sa.orm.mapper_registry.has_key(ClassKey(Packages, self.entity_name)):
            dmapper['packages'] = \
                    sa.mapper(Packages, sa.Table('packages', self.metadata, autoload=True), entity_name=self.entity_name)

        if not sa.orm.mapper_registry.has_key(ClassKey(Partitions, self.entity_name)):
            dmapper['partitions'] = \
                    sa.mapper(Partitions, sa.Table('partitions', self.metadata, autoload=True), entity_name=self.entity_name)

        if not sa.orm.mapper_registry.has_key(ClassKey(Scripts, self.entity_name)):
            dmapper['scripts'] = \
                    sa.mapper(Scripts, sa.Table('scripts', self.metadata, autoload=True), entity_name=self.entity_name)

        
        if not sa.orm.mapper_registry.has_key(ClassKey(Repos, self.entity_name)):
            dmapper['repos'] = \
                    sa.mapper(Repos, sa.Table('repos', self.metadata, autoload=True), \
                              properties={'nodegroups':sa.relation(NodeGroups, entity_name=self.entity_name), \
                                          'kits':sa.relation(Kits, secondary=dtable['repos_have_kits'], entity_name=self.entity_name)}, \
                              entity_name=self.entity_name)

        self.tables = dmapper.keys()

    def dropTables(self):
        """Drops all tables in the database"""

        self.metadata.drop_all()
 
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
            sa.Column('netname', sa.String(255)),
            sa.Column('startip', sa.String(45)),
            sa.Column('inc', sa.Integer, sa.PassiveDefault('1')),
            sa.Column('usingdhcp', sa.Boolean, sa.PassiveDefault('0')),
            mysql_engine='InnoDB')

        # You don't really idcomp2ng because this is 
        # a junction table for a M-N relantionship.
        # (ngid | cid) is uniq  
        ng_has_comp = sa.Table('ng_has_comp', self.metadata,
            sa.Column('idcomp2ng', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('ngid', sa.Integer, primary_key=True, nullable=False),
            sa.Column('cid', sa.Integer, primary_key=True, nullable=False),
            sa.ForeignKeyConstraint(['ngid'], ['nodegroups.ngid']),
            sa.ForeignKeyConstraint(['cid'], ['components.cid']),
            mysql_engine='InnoDB')
        sa.Index('comp2ng_FKIndex1', ng_has_comp.c.cid)
        sa.Index('comp2ng_FKIndex2', ng_has_comp.c.ngid)
       
        # Again, this is a M-N table. 
        ng_has_net = sa.Table('ng_has_net', self.metadata,
            sa.Column('idnet2ng', sa.Integer, primary_key=True, autoincrement=True),
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
            sa.Column('nid', sa.Integer, primary_key=True, nullable=False),
            sa.Column('netid', sa.Integer, primary_key=True, nullable=False),
            sa.Column('mac', sa.String(45)),
            sa.Column('ip', sa.String(20)),
            sa.Column('boot', sa.Boolean, sa.PassiveDefault('0')),
            sa.ForeignKeyConstraint(['nid'], ['nodes.nid']),
            sa.ForeignKeyConstraint(['netid'], ['networks.netid']),
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
            sa.Column('ngname', sa.String(45)),
            sa.Column('installtype', sa.String(20)),
            sa.Column('ngdesc', sa.String(255)),
            sa.Column('nameformat', sa.String(45)),
            sa.Column('kernel', sa.String(255)),
            sa.Column('initrd', sa.String(255)),
            sa.Column('kparams', sa.String(255)),
            mysql_engine='InnoDB')
        sa.Index('nodegroups_FKIndex1', nodegroups.c.repoid)

        nodes = sa.Table('nodes', self.metadata,
            sa.Column('nid', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('ngid', sa.Integer, sa.ForeignKey('nodegroups.ngid'), nullable=False),
            sa.Column('name', sa.String(45)),
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
            sa.Column('ngid', sa.Integer, primary_key=True),
            sa.Column('packagename', sa.String(255)),
            sa.ForeignKeyConstraint(['ngid'],
                                    ['nodegroups.ngid']),
            mysql_engine='InnoDB')
        sa.Index('packages_FKIndex1', packages.c.ngid)

        partitions = sa.Table('partitions', self.metadata,
            sa.Column('idpartitions', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('ngid', sa.Integer, primary_key=True),
            sa.Column('partition', sa.String(255)),
            sa.Column('mntpnt', sa.String(255)),
            sa.Column('fstype', sa.String(20)),
            sa.Column('size', sa.String(45)),
            sa.Column('options', sa.String(255)),
            sa.Column('preserve', sa.String(1)),
            sa.ForeignKeyConstraint(['ngid'],
                                    ['nodegroups.ngid']),
            mysql_engine='InnoDB')
        sa.Index('partitions_FKIndex1', partitions.c.ngid)

        repos = sa.Table('repos', self.metadata,
            sa.Column('repoid', sa.Integer, primary_key=True, autoincrement=True),
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

        self._load()

    def bootstrap(self):
        """bootstrap the necessary tables and fields that 
           are necessary for Kusu
        """
        import re
        session = sa.create_session()

        #######################################
        # change me. Bad to hardcode here. 
        #######################################
        #installer_name = 'example.com'
        #kit_name = 'base'
        #kit_version = '0.1'

        #kusu_dist = os.environ.get('KUSU_DIST', None)
        #kusu_distver = os.environ.get('KUSU_DISTVER', None)
        
        #pattern = re.compile('^i[3456]86$')        
        #if pattern.search(os.uname()[4]):
        #    arch = 'i386'
        #else:
        #    arch = os.uname()[4]

        #os_str = '%s-%s-%s' % (kusu_dist, kusu_distver, arch)
        #aRepo = Repos('The default repo for %s' % os_str, '', installer_name, os_str)
        #session.save(aRepo)
        #session.flush()

        #akit = session.query(self.kits).get_by(rname=kit_name, arch=arch, version=kit_version)

        #if akit:
            # Bad idea to use [0] as the kit name is not unique
        #    session.save(ReposHaveKits(aRepo.repoid, aKit[0].kid))

        session.save(NodeGroups(ngname='installer'))
        session.save(NodeGroups(ngname='compute'))
        session.flush()

        session.close()

    def createDatabase(self):
        """Creates the database"""

        if self.driver == 'mysql':
            try:
                if self.password:
                    cmd = 'mysql -u %s -p%s -h %s -P %s -e "create database %s;"' % \
                          (self.username, self.password, self.host, self.port, self.db)
                    print cmd
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
                raise CommandFailedToRun

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
                raise CommandFailedToRun

            if retcode:
                raise FailedToDropDatabase, 'Unable to drop database: %s' % self.db

        else:
            raise NotSupportedDatabaseCreationError, 'Database creation not supported for %s' % self.driver

    def destroy(self):
        pass

    def createSession(self):
        """Returns a sqlalchemy session"""

        return sa.create_session()

    def copyTo(self, other_db):
        """Copies the content of current database to
           a new database
        """
        if not isinstance(other_db, DB):
            raise Exception

        session = self.createSession()

        if other_db.driver == 'mysql':
            try:
                other_db.dropDatabase()
            except: pass
            other_db.createDatabase()

        # Creates the tables
        other_db.createTables()

        for table in self.tables:
            print table
            for obj in session.query(getattr(self, table)).select():
                try:
                    session.expunge(obj)
                except: pass

                # Fully detatch the object
                if hasattr(obj, '_instance_key'):
                    delattr(obj, '_instance_key')
                session.save_or_update(obj, entity_name=other_db.entity_name)

        session.flush()
        session.close()

if __name__ == '__main__':
    import os

    try:
        os.unlink('/tmp/f.db')
    except: pass

    k = DB('sqlite', '/tmp/f.db')
    k.create()
    k.bootstrap()

    session = sa.create_session()

    session.save(AppGlobals(kname='kname1', kvalue='kvalue1', ngid='ngid1'))
    session.save(AppGlobals(kname='kname2', kvalue='kvalue2', ngid='ngid2'))
    session.save(AppGlobals(kname='kname3', kvalue='kvalue3', ngid='ngid3'))
    
    myKit = Kits(rname='fedora-6-i386', rdesc='OS kit for fedora 6 i386',
                 version='6', isOS=True, removable=False, arch='i386')
    myKit.components.append(Components(cname='A component', os='os'))
    session.save(myKit)
    session.flush()

    myRepo = Repos(reponame='default-repo', installers='example.com',
                   ostype='fedora-6-i386')
    anotherRepo = Repos(reponame='another-repo', installers='example.org',
                   ostype='fedora-6-x86_64')
    session.save(myRepo)
    session.flush()
    
    session.save(NodeGroups(repoid=myRepo.repoid, ngname='myNodeGroup1'))
    session.save(NodeGroups(repoid=myRepo.repoid, ngname='myNodeGroup2'))

    anotherRepo.nodegroups.append(NodeGroups(ngname='myNodeGroup3'))
    session.save(anotherRepo)
    session.flush()

    session.save(ReposHaveKits(kid=myKit.kid, repoid=myRepo.repoid))
    session.save(ReposHaveKits(kid=myKit.kid, repoid=anotherRepo.repoid))
    session.flush()
     
    # all the nodegroups of all repos
    for repo in session.query(k.repos).select():
        print repo
        for nodegroup in repo.nodegroups:
            print '\t', nodegroup
    
    print
    print
    # all the kits for all repos, then
    #  all the components in a kit
    for repo in session.query(k.repos).select():
        print repo
        for kit in repo.kits:
            print '\t', kit
            for component in kit.components:
                print '\t\t', component

    print
    print   
    for kit in session.query(k.kits).select():
        print kit
        for repo in kit.repos:
            print '\t', repo

    print
    print
    # Get agid=1
    app1 = session.query(k.appglobals).get(1)
    print app1
    app1.kname = 'this has been changed'
    session.save(app1)
    session.flush
    print session.query(k.appglobals).get(1)
    
    session.delete(app1) # bye bye
    session.flush()
    print session.query(k.appglobals).get(1) # returns None
