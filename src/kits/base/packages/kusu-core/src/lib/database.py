#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import os
import time
import path
import warnings
import logging
import sqlalchemy as sa
from sqlalchemy.ext.sessioncontext import SessionContext
from sqlalchemy.ext.assignmapper import assign_mapper
from kusu.util.errors import *
import kusu.util.log as kusulog
from primitive.system.software.dispatcher import Dispatcher
from primitive.support.osfamily import getOSNames, matchTuple
from kusu.util.kits import processKitInfo, SUPPORTED_KIT_APIS
from sets import Set

logging.getLogger('sqlalchemy').parent = kusulog.getKusuLog()

SUPPORTED_KIT_APIS = ['0.2', '0.3', '0.4']

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
    cols = ['kid', 'cname', 'cdesc', 'os', 'ngtypes']

    def getNGTypes(self, match_empty_ngtypes=True):
        # match_empty_ngtypes=False is used to mimic kitops' component ngtypes (Kit ASK 0.2 bug)
        #     i.e. '*' denotes match against All ngtypes; and None or '' denote match against None
        if self.ngtypes == '*' or \
            (match_empty_ngtypes and (not self.ngtypes or self.ngtypes.strip() == '')):
            return ['installer','compute','compute-diskless', 'compute-imaged', 'other']

        elif not self.ngtypes or self.ngtypes.strip() == '':
            return []
        else:
            return self.ngtypes.split(';')

    def __repr__(self):
        return '%s(%r,%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.kid, self.cname, self.os, self.ngtypes,
                self.cdesc)

class DriverPacks(BaseTable):
    cols = ['dpid', 'cid', 'dpname', 'dpdesc']
    def __repr__(self):
        return '%s(%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.dpid, self.cid, self.dpname, self.dpdesc)

class Kits(BaseTable):
    cols = ['rname', 'rdesc', 'version', 'isOS', \
            'removable', 'arch', 'osid', 'release']

    def getMatchingComponents(self, target_os):

        if self.is_os():
            if self.os == target_os:
                return self.components
            else:
                return []

        components_list = []
        os_string = '%s-%s-%s' % (target_os.name, target_os.major, target_os.arch)
        os_string = os_string.lower()

        repo_os = (target_os.name, target_os.major, target_os.minor, target_os.arch)

        try:
            kits_root = AppGlobals.selectfirst_by(kname='DEPOT_KITS_ROOT').kvalue
        except AttributeError:
            kits_root = '/depot/kits'

        kit_path = path.path(kits_root)
        kitinfo = kit_path / str(self.kid) / 'kitinfo'
        infokit, infocomps = processKitInfo(str(kitinfo))

        if len(infokit) == 0 or 'api' not in infokit or '0.1' == infokit['api']:
            lst = [comp for comp in self.components if not comp.os or \
                   comp.os.lower() == os_string or comp.os.lower() == os.name.lower() or \
                   comp.os.strip() == '' or comp.os == 'NULL']
            components_list.extend(lst)

        elif infokit['api'] in SUPPORTED_KIT_APIS:
            comp_dict = {}
            for db_comp in self.components:
                comp_dict[db_comp.cname] = db_comp

            for comp in infocomps:
                os_tuples = []

                try:
                    for tup in comp['os']:
                        for os_name in getOSNames(tup['name'], default=[tup['name']]):
                            os_tuples.append((os_name, tup['major'], tup['minor'], tup['arch']))
                except KeyError:
                    break

                try:
                    if comp['pkgname'] in comp_dict and matchTuple(repo_os, os_tuples):
                        components_list.append(comp_dict[comp['pkgname']])
                except KeyError: pass

        return components_list

    def getSupportedDistro(self):

        if self.is_os():
            return [self.os]

        os_set = Set()
        try:
            kits_root = AppGlobals.selectfirst_by(kname='DEPOT_KITS_ROOT').kvalue
        except AttributeError:
            kits_root = '/depot/kits'

        kit_path = path.path(kits_root)
        kitinfo = kit_path / str(self.kid) / 'kitinfo'
        infokit, infocomps = processKitInfo(str(kitinfo))

        if len(infokit) == 0 or 'api' not in infokit or '0.1' == infokit['api']:
            for comp in self.components:
                if not comp.os or comp.os.strip() == '' or comp.os == 'NULL':
                    return None

                else:
                    os_set.add(comp.os.lower())
                     
        elif infokit['api'] in SUPPORTED_KIT_APIS:
            for comp in infocomps:
                try:
                    for tup in comp['os']:
                        for os_name in getOSNames(tup['name'], default=[tup['name']]):

                            os_str = os_name
                            if tup['minor'] == '*':
                                os_str = os_str + '-' + tup['major']
                            else:
                                os_str = os_str + '-' + tup['major'] + '.' + tup['minor']

                            if tup['arch'] in ['*', 'noarch']:
                                os_set.add(os_str + '-' + 'i386')
                                os_set.add(os_str + '-' + 'x86_64')
                            else:
                                os_set.add(os_str + '-' + tup['arch'])
                except KeyError:
                    break
        return sorted(os_set)

    def is_os(self):
        if self.osid is not None or self.isOS:
            return True
        else:
            return False

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
        return '%s(%r,%r,%r,%r,%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.rname, self.version, self.release,
                self.arch, self.rdesc, self.isOS, self.osid, self.removable)

class Modules(BaseTable):
    cols = ['ngid', 'module', 'loadorder']
    def __repr__(self):
        return '%s(%r,%r,%r)' % \
               (self.__class__.__name__, self.ngid, self.module, self.loadorder)

class Networks(BaseTable):
    cols = ['network', 'subnet', 'device', 'suffix', \
            'gateway', 'options', 'netname', 'startip', \
            'inc', 'type', 'usingdhcp']
    types = ['public', 'provision']
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
    types = ['installer', 'compute', 'compute-imaged', 'compute-diskless', 'other']

    def getEligibleComponents(self, match_empty_ngtypes=True):
        """Returns a list of components eligible for a nodegroup"""

        if self.repoid is None:
            return []

        # match_empty_ngtypes=False is used to mimic kitops' component associability criteria.
        #     It filters out components with None or '' ngtype.
        # match_empty_ngtypes=True matches components with None or '' ngtype.
        return self.repo.getEligibleComponents(ngtype=self.type, match_empty_ngtypes=match_empty_ngtypes)

    def __repr__(self):
        return '%s(%r,%r,%r,%r,%r,%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.ngname, self.repoid, self.type,
                self.installtype, self.ngdesc, self.nameformat, self.kernel,
                self.initrd, self.kparams)

class Nodes(BaseTable):
    cols = ['ngid', 'name', 'kernel', 'initrd', \
            'kparams', 'state', 'bootfrom', 'lastupdate', \
            'rack', 'rank', 'uid']
    def __repr__(self):
        return '%s(%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r)' % \
               (self.__class__.__name__, self.ngid, self.name, self.kernel,
                self.initrd, self.kparams, self.state, self.bootfrom,
                self.lastupdate, self.rack, self.rank, self.uid)

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
             if kit.is_os():
                 return kit.os
        return None

    os = property(getOS)

    def getOSKit(self):
        for kit in self.kits:
             if kit.is_os():
                 return kit
        return None

    oskit = property(getOSKit)

    def getEligibleComponents(self, ngtype=None, match_empty_ngtypes=True):
        """Returns a list of components eligible for a nodegroup type.
           If ngtype is None, it returns all components in the repo.
        """

        components_list = []

        for kit in self.kits:
            if kit.is_os():
                components_list.extend(kit.components)
            else:
                matched = kit.getMatchingComponents(self.os)
                eligible = matched
                if ngtype is not None:
                    # match_empty_ngtypes=False is used to mimic kitops' component associability criteria.
                    #     It filters out components with None or '' ngtype.
                    # match_empty_ngtypes=True matches components with None or '' ngtype.
                    eligible = [comp for comp in matched if ngtype in comp.getNGTypes(match_empty_ngtypes=match_empty_ngtypes)]
                components_list.extend(eligible)

        return components_list

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

class AlterEgos(BaseTable):
    cols = ['mac', 'ngid', 'name', 'ip', 'rack', 'rank', 'bmcip']
    def __repr__(self):
        return '%s(%r, %r, %r, %r, %r, %r, %r)' % \
                (self.__class__.__name__, self.mac, self.ngid, \
                 self.name, self.ip, self.rack, self.rank, self.bmcip)

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
                    'OS' : OS,
                    'AlterEgos' : AlterEgos}

    __passfile = os.environ.get('KUSU_ROOT', '') + '/etc/db.passwd'
    __postgres_passfile = os.environ.get('KUSU_ROOT', '') + '/etc/pgdb.passwd'

    def __init__(self, driver, db=None, username=None, password=None,
                 host='localhost', port=None, entity_name=None):
        """Initialize the database with the correct driver and account
           details"""

        if not db and driver == 'sqlite':
            raise NoSuchDBError, 'Must specify db for driver: %s' % driver

        apache_password = ''
        if username == 'apache':
            apache_password = self.__getPasswd()
        if apache_password:
            password = apache_password

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

            if password:
                engine_src += ':%s@%s:%s/%s' % (password, host, port, db)
            else:
                engine_src += '@%s:%s/%s' % (host, port, db)

        elif driver == 'postgres':

            if username == 'postgres':
                postgres_password = self.__getPasswd(user='postgres')
                if postgres_password: #ensure postgres_password
                    password = postgres_password

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

    def __getPasswd(self, user='apache'):
        """
        Open self.__passfile to retrieve password, return None on fail.
        """

        if user == 'postgres':
            passfile = self.__postgres_passfile
        else:
            passfile = self.__passfile

        try:
            fp = file(passfile, 'r')
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
            sa.Column('os', sa.String(255)),
            sa.Column('ngtypes', sa.String(255)),
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
            sa.Column('release', sa.Integer, default=1),
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
            sa.Column('ngname', sa.String(255), unique=True),
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
            sa.Column('uid', sa.String(255)),
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
            sa.Column('ostype', sa.String(255)),
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

        alteregos = sa.Table('alteregos', self.metadata,
            sa.Column('alteregoid', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('mac', sa.String(45)),
            sa.Column('ngid', sa.Integer),
            sa.Column('name', sa.String(45)),
            sa.Column('ip', sa.String(20)),
            sa.Column('rack', sa.Integer, sa.PassiveDefault('0')),
            sa.Column('rank', sa.Integer, sa.PassiveDefault('0')),
            sa.Column('bmcip', sa.String(20)),
            mysql_engine='InnoDB')
        sa.Index('alteregos_FKIndex1', alteregos.c.alteregoid)
        self.__dict__['alteregos'] = alteregos

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
        assign_mapper(self.ctx, DriverPacks, driverpacks,
          properties={'component': sa.relation(Components, entity_name=self.entity_name)},
          entity_name=self.entity_name)

        kits = sa.Table('kits', self.metadata, autoload=True)
        assign_mapper(self.ctx, Kits, kits,
          properties={'components': sa.relation(Components,
                                                entity_name=self.entity_name),
                      'os': sa.relation(OS, entity_name=self.entity_name),
                      'repos': sa.relation(Repos, secondary=repos_have_kits,
                                           entity_name=self.entity_name),
                      'removable': kits.c.removeable},
          entity_name=self.entity_name)

        modules = sa.Table('modules', self.metadata, autoload=True)
        assign_mapper(self.ctx, Modules, modules,
          properties={'nodegroup': sa.relation(NodeGroups, entity_name=self.entity_name)},
          entity_name=self.entity_name)

        ng_has_net = sa.Table('ng_has_net', self.metadata, autoload=True)
        assign_mapper(self.ctx, NGHasNet, ng_has_net,
                      entity_name=self.entity_name)

        networks = sa.Table('networks', self.metadata, autoload=True)
        assign_mapper(self.ctx, Networks, networks,
          properties={'nics': sa.relation(Nics, entity_name=self.entity_name),
                      'nodegroups': sa.relation(NodeGroups,
                                                secondary=ng_has_net,
                                                entity_name=self.entity_name)},
          entity_name=self.entity_name)

        nics = sa.Table('nics', self.metadata, autoload=True)
        assign_mapper(self.ctx, Nics, nics,
          properties={'network': sa.relation(Networks, entity_name=self.entity_name),
                      'node': sa.relation(Nodes, entity_name=self.entity_name)},
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
                                              entity_name=self.entity_name),
                      'scripts': sa.relation(Scripts,
                                             entity_name=self.entity_name),
                      'repo': sa.relation(Repos,
                                          entity_name=self.entity_name)},

          entity_name=self.entity_name)

            # Currently nodegroups <-> components relationship is defined twice.
            # Possible to replace this with ingenious backref-fu.

        nodes = sa.Table('nodes', self.metadata, autoload=True)
        assign_mapper(self.ctx, Nodes, nodes,
          properties={'nics': sa.relation(Nics, entity_name=self.entity_name),
                      'nodegroup': sa.relation(NodeGroups, entity_name=self.entity_name)},
          entity_name=self.entity_name)

        packages = sa.Table('packages', self.metadata, autoload=True)
        assign_mapper(self.ctx, Packages, packages,
          properties={'nodegroup': sa.relation(NodeGroups, entity_name=self.entity_name)},
          entity_name=self.entity_name)

        partitions = sa.Table('partitions', self.metadata, autoload=True)
        assign_mapper(self.ctx, Partitions, partitions,
          properties={'nodegroup': sa.relation(NodeGroups, entity_name=self.entity_name)},
          entity_name=self.entity_name)

        scripts = sa.Table('scripts', self.metadata, autoload=True)
        assign_mapper(self.ctx, Scripts, scripts,
          properties={'nodegroup': sa.relation(NodeGroups, entity_name=self.entity_name)},
          entity_name=self.entity_name)

        repos = sa.Table('repos', self.metadata, autoload=True)
        assign_mapper(self.ctx, Repos, repos,
          properties={'nodegroups': sa.relation(NodeGroups,
                                                entity_name=self.entity_name),
                      'kits': sa.relation(Kits, secondary=repos_have_kits,
                                          entity_name=self.entity_name)},
          entity_name=self.entity_name)

        alteregos = sa.Table('alteregos', self.metadata, autoload=True)
        assign_mapper(self.ctx, AlterEgos, alteregos,
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

            imaged = NodeGroups(ngname='compute-imaged', nameformat='host#NNN',
                                installtype='disked', type='compute-imaged')
            imaged.kparams = compute.kparams
  
            # creates the necessary modules for imaged nodes
            for index, mod in enumerate(Dispatcher.get('imaged_modules', default=[])):
                imaged.modules.append(Modules(loadorder=index+1, module=mod))

            # Creates the necessary pkg list for imaged nodes
            for pkg in Dispatcher.get('imaged_packages', default=[]):
                imaged.packages.append(Packages(packagename=pkg))

        if kusu_dist in getOSNames('rhelfamily') + ['sles']:
            diskless = NodeGroups(ngname='compute-diskless', nameformat='host#NNN',
                                  installtype='diskless', type='compute-diskless')
            diskless.kparams = compute.kparams

            # creates the necessary modules for diskless nodes
            for index, mod in enumerate(Dispatcher.get('diskless_modules', default=[])):
                diskless.modules.append(Modules(loadorder=index+1, module=mod))

            # Creates the necessary pkg list for diskless nodes
            for pkg in Dispatcher.get('diskless_packages', default=[]):
                diskless.packages.append(Packages(packagename=pkg))

        NodeGroups(ngname='unmanaged', nameformat='device#NNN',
                   installtype='unmanaged', type='other')

        # Create the master installer node
        now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        master_node = Nodes(name='master', state='Installed', lastupdate=now, bootfrom=true, uid='')
        installer.nodes.append(master_node)

        # Create the partition entries for the compute node
        # REGULAR PARTITIONING

        # use literals so we can overcome mysql and postgres specifics
        default_fstype = Dispatcher.get('default_fstype', default='ext3')
        for ng in [compute]:
            boot = Partitions(mntpnt='/boot', fstype='ext3', partition='1',
                              size='100', device='1', preserve=false)
            root = Partitions(mntpnt='/', fstype=default_fstype, partition='2',
                              size='12000', device='1', preserve=false)
            swap = Partitions(fstype='linux-swap', partition='3',
                              size='2000', device='1', preserve=false)
            var = Partitions(mntpnt='/var', fstype=default_fstype, partition='5',
                             size='2000', device='1', preserve=false)
            data = Partitions(mntpnt='/data', fstype=default_fstype, partition='6', size='14000',
                              options='fill', device='1', preserve=false)
            donotpreserve = Partitions(options='partitionID=*', preserve=false)
            ng.partitions.append(boot)
            ng.partitions.append(root)
            ng.partitions.append(swap)
            ng.partitions.append(var)
            ng.partitions.append(data)
            ng.partitions.append(donotpreserve)

        # Imaged Partitioning
        boot = Partitions(mntpnt='/boot', fstype='ext2', partition='1',
                          size='100', device='1', preserve=false)
        swap = Partitions(fstype='linux-swap', partition='2',
                          size='8000', device='1', preserve=false)
        root = Partitions(mntpnt='/', fstype=default_fstype, partition='3',
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
        root = Partitions(mntpnt='/', fstype=default_fstype, size='12000',
                          device='ROOT', options='lv;vg=KusuVolGroup00', preserve=false)
        depot = Partitions(mntpnt='/depot', fstype=default_fstype, size='10000',
                           device='DEPOT', options='lv;vg=KusuVolGroup00', preserve=false)
        var = Partitions(mntpnt='/var', fstype=default_fstype, size='2000',
                         device='VAR', options='lv;vg=KusuVolGroup00', preserve=false)

#        dell = Partitions(options='partitionID=Dell Utility', preserve=true)
# We no longer need to preserve dell UP        
        donotpreserve = Partitions(options='partitionID=*', preserve=false)
        for parts in [boot, swap, pv, vg, root, depot, var, donotpreserve]:
            installer.partitions.append(parts)
        # End Installer Partitioning Schema

        # default appglobals values
        AppGlobals(kname='CFMBaseDir', kvalue='/opt/kusu/cfm')
        AppGlobals(kname='InstallerServeDNS', kvalue='1')
        AppGlobals(kname='InstallerServeDHCP', kvalue='1')
        AppGlobals(kname='InstallerServeNIS', kvalue='0')
        AppGlobals(kname='InstallerServeNTP', kvalue='1')
        AppGlobals(kname='InstallerServeNFS', kvalue='1')
        AppGlobals(kname='KusuAuthScheme', kvalue='files')
#        AppGlobals(kname='ImageBaseDir', kvalue='/depot/images')
        AppGlobals(kname='DEPOT_KITS_ROOT', kvalue='/depot/kits')
        AppGlobals(kname='DEPOT_DOCS_ROOT', kvalue='/depot/www/kits')
        AppGlobals(kname='DEPOT_IMAGES_ROOT', kvalue='/depot/images')
        AppGlobals(kname='DEPOT_REPOS_ROOT', kvalue='/depot/repos')
        AppGlobals(kname='DEPOT_REPOS_SCRIPTS', kvalue='/depot/repos/custom_scripts/')
        AppGlobals(kname='DEPOT_REPOS_POST', kvalue='/depot/repos/post_scripts')
        AppGlobals(kname='DEPOT_CONTRIB_ROOT', kvalue='/depot/contrib')
        AppGlobals(kname='DEPOT_UPDATES_ROOT', kvalue='/depot/updates')
        AppGlobals(kname='DEPOT_AUTOINST_ROOT', kvalue='/depot/repos/instconf')
        AppGlobals(kname='PIXIE_ROOT', kvalue='/tftpboot/kusu')
        AppGlobals(kname='PROVISION', kvalue='KUSU')
        AppGlobals(kname='PRESERVE_NODE_IP', kvalue='0')
        AppGlobals(kname='MASTER_UUID', kvalue='KUSU')
        AppGlobals(kname='KUSU_VERSION', kvalue='${VERSION_STR}')
        AppGlobals(kname='InstNum', kvalue='')
        AppGlobals(kname='LMGRD_PATH', kvalue='')
        AppGlobals(kname='LM_LICENSE_FILE', kvalue='')
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
                password = self.__getPasswd(user='postgres')
                env = os.environ.copy()
                env['PGPASSWORD'] = password

                # ignore self.password for now
                # expect to have a psql create role apache with superuser login to be run
                # already.
                cmd = 'psql -p %s  postgres %s   -c "create database %s with owner = %s;"'\
                      % (self.port, self.username, self.db, self.username)
                p = subprocess.Popen(cmd,
                                     shell=True,
                                     env=env,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                out, err = p.communicate()
                retcode = p.returncode
            except Exception, e:
                raise CommandFailedToRunError, e

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
                password = self.__getPasswd(user='postgres')
                env = os.environ.copy()
                env['PGPASSWORD'] = password

                # ignore self.password for now
                # expect to have a psql create role apache with superuser login to be run
                # already.
                cmd = 'psql -p %s  postgres %s   -c "drop database %s;"'\
                        % (self.port,self.username,self.db)

                p = subprocess.Popen(cmd,
                                     shell=True,
                                     env=env,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                out, err = p.communicate()
                retcode = p.returncode

            except Exception, e:
                    raise CommandFailedToRunError, e

            if retcode:
                raise CommandFailedToRunError, 'Failed to drop database'

        else:
            raise NotSupportedDatabaseCreationError, 'Database creation not supported for %s' % self.driver

    def destroy(self):
        pass

    def createSession(self):
        """Returns a sqlalchemy session"""

        return sa.create_session()

    def expire_all(self):
        sess = self.ctx.get_current()
        sess.clear()

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
        if not other_db.driver == 'sqlite':
            other_db.createDatabase()
            other_db.dropTables()

        # Creates the tables
        other_db.createTables()

        # Copy them in order to preserve relationship
        # Order by primary, secondary(1-M) and
        # junction tables(M-N)
        for table in ['AppGlobals', 'AlterEgos', 'Repos', 'OS', 'Kits', 'Networks', \
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

    def is_connection_valid(self):
        """Checks the DB connection.

        Returns True if the connection is valid, False otherwise."""

        if self.driver == 'postgres':
            password = self.__getPasswd(user='postgres')
            env = os.environ.copy()
            env['PGPASSWORD'] = password

            # We execute an empty command. If the DB isn't yet ready, we'll get
            # a non-zero return code.
            cmd = ['psql', '-p', self.port, 'postgres', 'postgres', '-c', '']
            checkP = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            o, e = checkP.communicate()
            return 0 == checkP.returncode

        # Other DBs not yet implemented
        return True

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

def findNodeGroupsFromComponent(db, columns=[], compargs={}, ngargs={}):
    """
    Selects nodegroups which has associated components
    SELECT cols FROM nodegroups
    WHERE components <-> ng_has_comp <-> nodegroups

    columns -- a list of kits columns to select; set to [] to select all.
    compargs -- a dictionary of components columns to match in WHERE clause
    ngargs -- a dictionary of nodegroups columns to match in WHERE clause
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
                           db.ng_has_comp.c.cid == db.components.c.cid))

    for arg in ngargs:
        if db.nodegroups.c.has_key(arg) and ngargs[arg] is not None:
            stmt.append_whereclause(getattr(db.nodegroups.c, arg) == \
                                    ngargs[arg])
        elif not db.nodegroups.c.has_key(arg):
            raise NoSuchColumnError, \
                "Invalid column '%s' for table '%s'" % (arg, db.nodegroups.name)

    for arg in compargs:
        if db.components.c.has_key(arg) and compargs[arg] is not None:
            stmt.append_whereclause(getattr(db.components.c, arg) == compargs[arg])
        elif not db.components.c.has_key(arg):
            raise NoSuchColumnError, \
                "Invalid column '%s' for table '%s'" % (arg, db.components.name)

    return stmt.execute().fetchall()
