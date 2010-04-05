import sys
import os
import time
import tempfile
import filecmp
import atexit
import subprocess
from path import path
from kusu.core.database import DB
from kusu.core.app import KusuApp
from kusu.util.errors import *
from primitive.support.util import *

import primitive.support.log as primitivelog
pl = primitivelog.getPrimitiveLog()
pl.addFileHandler('/var/log/kusu/kusu-migrate.log')
pl = primitivelog.getPrimitiveLog('kusu-migrate')

PCM_1_2 = '1.2'
PCM_2_0 = '2.0'
COMPONENT_LSF_MASTER = 'component-LSF-Master'
LSF = 'LSF'
KUSU_VERSION_APPGLOBALS_KEY = 'KUSU_VERSION'
DEPOT_REPOS_SCRIPTS_APPGLOBALS_KEY = 'DEPOT_REPOS_SCRIPTS'
DEPOT_REPOS_POST_APPGLOBALS_KEY = 'DEPOT_REPOS_POST'
DEPOT_CONTRIB_ROOT_APPGLOBALS_KEY = 'DEPOT_CONTRIB_ROOT'

class KusuMigrateDB(DB):
    def copyTo(self, other_db):
        """Copies the content of current database to
           a new database. Existing tables and data on
           the new database will be deleted.
        """

        if not isinstance(other_db, DB):
            raise TypeError, "Class '%s' is not a DB class" % other_db.__class__.__name__

        if other_db.driver in ['mysql', 'postgres']:
            try:
                other_db.dropDatabase()
            except: pass

        if not other_db.driver == 'sqlite':
            other_db.createDatabase()
            other_db.dropTables()
        # Creates the tables
        other_db.createTables()

        # Copy them in order to preserve relationship
        # Order by primary, secondary(1-M) and 
        # junction tables(M-N)
        for table in ['AppGlobals', 'Repos', 'Kits', 'Networks', \
                      'Components', 'NodeGroups', 'Modules', \
                      'Nodes', 'Packages', 'Partitions', 'Scripts', 'DriverPacks', \
                      'Nics', 'NGHasComp', 'ReposHaveKits', 'NGHasNet']:
            for obj in getattr(self, table).select():
                try:
                    obj.expunge()
                except: pass

                # Fully detatch the object
                if hasattr(obj, '_instance_key'):
                    delattr(obj, '_instance_key')
                try:
                    obj.save_or_update(entity_name=other_db.entity_name)
                    obj.flush()
                except Exception ,e :
                    raise UnableToSaveDataError, obj
            if other_db.driver =='postgres':
                other_db.postgres_update_sequences(other_db.postgres_get_seq_list())


class KusuMigrate:


    def __init__(self, **kw):
        engine = os.getenv('KUSU_DB_ENGINE')
        if engine == 'mysql':
            dbdriver = 'mysql'
        else:
            dbdriver = 'postgres'
        self.db = KusuMigrateDB(dbdriver, db='kusudb', username='apache')

        self.custom_scripts_dir = \
                   self._get_appglobals(DEPOT_REPOS_SCRIPTS_APPGLOBALS_KEY, \
                                        '/depot/repos/custom_scripts')
        self.post_scripts_dir = \
                 self._get_appglobals(DEPOT_REPOS_POST_APPGLOBALS_KEY, \
                                      '/depot/repos/post_scripts')
        self.custom_packages_dir = \
                 self._get_appglobals(DEPOT_CONTRIB_ROOT_APPGLOBALS_KEY, \
                                      '/depot/contrib')
        
    def doExportAction(self, tgzfile):
        if not self._kusu_version(self.db) == PCM_1_2:
            print "kusu-migrate --export can only be invoked in PCM 1.2"
            sys.exit(1)

        if not self._is_red_hat_distro():
            print "kusu-migrate is only applicable for PCM RHEL edition."
            sys.exit(1)

        workspace_dir = path(tempfile.mkdtemp(prefix='kusu-migrate'))
        atexit.register(self.cleanup, workspace_dir)
        migrate_dir = workspace_dir/'kusu-migrate'
        migrate_dir.makedirs()

        print "Copying Database..."
        migrate_db = migrate_dir / 'kusudb_copy.db'
        m_db = DB('sqlite', migrate_db, entity_name='alt')
        self.db.copyTo(m_db)
        pl.info("copy kusu database completed.")

        print "Copying custom scripts..."
        self.copyDirectory(self.custom_scripts_dir, migrate_dir)
        pl.info("copy custom scripts from %s completed."\
                                      % self.custom_scripts_dir)
        print "Copying post scripts..."
        self.copyDirectory(self.post_scripts_dir, migrate_dir)
        pl.info("copy post scripts from %s completed." \
                                            % self.post_scripts_dir)
        if  self._is_lsf_installed(self.db):
            print "LSF kit was detected..."
            pl.info("detected lsf kit")
            self.exportLSFConfiguration(self.db, migrate_dir)

        if not self.sufficientDiskSpace(migrate_dir, self.custom_packages_dir):
            print "Custom packages are not copied due to insufficient disk " \
                  "space."
        else:
            print "Copying custom packages..."
            self.copyDirectory(self.custom_packages_dir, migrate_dir)
            pl.info("copy custom packages from %s completed." \
                                                  % self.custom_packages_dir)
        print "Generating mac files for nodegroups..."
        self.generateMacFiles(self.db, migrate_dir /'mac_files')
        pl.info("generate mac files for all nodegroups completed.")

        print "Generating configuration report for cluster..."
        t = time.localtime()
        report = self.generateReport(self.db, t)
        pl.info("generate report for current cluster configuration completed.")
        report_file = migrate_dir / ('pcm1.2_migration_report-' \
                                             '%s%s%s-%s%s%s' % \
                                             (t.tm_year, t.tm_mon, t.tm_mday, \
                                              t.tm_hour, t.tm_min, t.tm_sec))
        self.createReportFile(report, report_file)
        pl.info("configuration report created in %s" % report_file)

        print "Running kusu-debug..."
        pl.info("start running kusu-debug...")
        stdout, stderr = runCommand('kusu-debug')
        if stdout:
            print stdout
            kdebug_path = path(stdout[stdout.rfind('/tmp/kusu-debug-'):\
                                                         stdout.rfind('\n')])
            if kdebug_path.exists():
                kdebug_path.move(migrate_dir)
                pl.info("copy kusu-debug tar-gzipped file for " \
                        "kusu-migrate --export.")
            pl.info("kusu-debug completed.")
        if stderr:
            pl.error(stderr)

        if not tgzfile:
            tgzfile = 'pcm1.2_migration-%s%s%s-%s%s%s.tgz' % \
                                       (t.tm_year, t.tm_mon, t.tm_mday, \
                                        t.tm_hour, t.tm_min, t.tm_sec)
        tgzfile_path = path(os.getcwd()) / tgzfile
        if not self.sufficientDiskSpace(tgzfile_path.splitpath()[0], migrate_dir):
            print "%s is not generated due to insufficient disk space in %s" \
                                               % (tgzfile_path.splitpath()[1],
                                                  tgzfile_path.splitpath()[0])
            sys.exit(1)
        if tgzfile_path.exists():
            tgzfile_path.remove()
        ctar_cmd = 'tar -zcf %s -C %s kusu-migrate ' % (tgzfile, workspace_dir)
        stdout, stderr = runCommand(ctar_cmd)
        if stdout:
            pl.info(stdout)
        if stderr:
            pl.info(stderr)
        pl.info("kusu-migrate --export has completed successfully.")
        print "Settings are migrated successfully into %s.\n\n" % tgzfile
        self.printExportPromptMessage(tgzfile)

    def doImportAction(self, tgzfile):
        if not self._kusu_version(self.db) == PCM_2_0:
            print "kusu-migrate --import can only be invoked in PCM 2.0"
            sys.exit(1)
        if not self._is_red_hat_distro():
            print "kusu-migrate is only applicable for PCM RHEL edition."
            sys.exit(1)
        if not self.sufficientDiskSpace('/depot', tgzfile):
            print "kusu-migrate --import cannot be invoked due to insufficient " \
                  "disk space in /depot"
            sys.exit(1)
        migrate_dir = path('/depot/kusu-migrate')
        if migrate_dir.exists():
            res = raw_input("kusu-migrate --import has been invoked before.\n" \
                            "Invoking kusu-migrate --import again will override " \
                            "the contents of /depot/kusu-migrate/ directory.\n" \
                            "Continue with kusu-migrate --import? (y/n)")
            if res.lower() in ['yes','y']:
                migrate_dir.rmtree()
            else:
                sys.exit(1)
        self.printImportPromptMessage(tgzfile)
        self._exit_if_no_tgzfile_found(tgzfile)

        print "Extracting information from %s to /depot/kusu-migrate/..." % tgzfile
        xtar_cmd = 'tar -zxf %s -C /depot' % tgzfile
        stdout, stderr = runCommand(xtar_cmd)
        if stdout:
            pl.info(stdout)
            pl.info("kusu-migrate --import extract information from %s " \
                    "to /depot/kusu-migrate/... completed." % tgzfile)
        if stderr:
            pl.error(stderr)

        if self._lsf_configuration_exists():
            print "Configuration files for Platform LSF kit are found."
            if self._is_lsf_installed(self.db):
                print "Platform LSF kit was detected..."
                pl.info("detected lsf kit")
                res = raw_input("Import Platform LSF configuration " \
                                "files? (y/n)")
                if res.lower() in ['yes','y']:
                    self.importLSFConfiguration(tgzfile)
            else:
                print "Platform LSF kit was not installed.\nConfiguration " \
                      "files for LSF kit in <%s> are not extracted to \n" \
                      "/etc/cfm/templates/lsf/ directory." % tgzfile
        print "Settings are extracted from %s successfully.\n\n" % tgzfile
        pl.info("kusu-migrate import has completed successfully.")

    def sufficientDiskSpace(self, target_dir, source_dir):
        try:
            stdout, stderr = runCommand("df %s" % target_dir)
        except:    
            return False
        if not stdout:
            return False
        free_diskspace = int(stdout.split('\n')[2].split()[2])
        try:
            stdout, stderr = runCommand("du -s %s" % source_dir)
        except:
            return False
        if not stdout:
            return False
        req_diskspace = int(stdout.split()[0])
        return free_diskspace > req_diskspace

    def printReportFile(self, tgzfile):
        self._exit_if_no_tgzfile_found(tgzfile)
        tmpdir = path(tempfile.mkdtemp(prefix='kusu-migrate'))
        atexit.register(self.cleanup, tmpdir)
        xtar_cmd = 'tar -zxf %s -C %s' % (tgzfile, tmpdir)
        stdout, stderr = runCommand(xtar_cmd)

        migrate_dir = tmpdir / 'kusu-migrate'
        report_file = migrate_dir.files(pattern='pcm1.2_migration_report-*')
        f= open(report_file[0])
        for line in f:
            sys.stdout.write(line)
        f.close()

    def exportLSFConfiguration(self, db, mdir):
        lsf_dir = path('/etc/cfm/templates/lsf')
        if lsf_dir.exists():
            print "Copying LSF kit configurations and templates..."
            self.copyDirectory(lsf_dir, mdir)
            pl.info("export lsf configurations from %s completed." % lsf_dir)
        lsf_license = path('/opt/lsf/conf/license.dat')
        lsf_license_dir = mdir / 'opt/lsf/conf'

        if lsf_license_dir.exists():
            lsf_license_dir.rmdir()
        lsf_license_dir.makedirs()

        nodegroups = db.AppGlobals.select_by(db.AppGlobals.c.kname.startswith(LSF),
                                             db.AppGlobals.c.kname.endswith('ClusterName'))
        comps = db.Components.select_by(db.Components.c.cname.startswith(COMPONENT_LSF_MASTER))
        compList = []
        for comp in comps:
            compList.append(comp.cid)

        for ng in nodegroups: 
            nodes = db.Nodes.filter_by(db.Nodes.c.ngid==ng.ngid, \
                                    ng.ngid==db.ng_has_comp.c.ngid, \
                                    db.ng_has_comp.c.cid.in_(*compList)).all()
            for n in nodes:
                nics = n.nics
                for nic in nics:
                    lsf_tmpdir = path(tempfile.mkdtemp(prefix='lsf-license'))
                    atexit.register(self.cleanup, lsf_tmpdir)
                    cmd = "scp root@%s:/opt/lsf/conf/license.dat %s" \
                                       % (nic.ip, lsf_tmpdir)
                    try:
                        p = subprocess.Popen(cmd,
                                             shell=True,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
                        stdout, stderr = p.communicate()
                    except OSError, e:
                        msg = "Unable to copy LSF license file from %s : %s" \
                                                         % (n.name, stderr)
                        print msg
                        pl.error(msg)
                        continue
                    if p.returncode:
                        msg = "No LSF license file is copied from %s : %s" \
                                                           % (n.name, stderr)
                        print msg
                        pl.error(msg)
                        continue
                    if stdout:
                        print stdout
                        pl.info(stdout)
                    if stderr:
                        pl.error(stderr)
                    lsf_l = lsf_tmpdir/'license.dat'
                    if lsf_l.exists():
                        lsf_l.copy(lsf_license_dir/('license.dat.%s' \
                                                            % (ng.kvalue)))
                        print "Copying LSF license file from %s, " \
                                         "ip address %s" % (n.name, nic.ip)
                        pl.info("copied lsf license from %s, ip address %s" \
                                                       % (n.name, nic.ip))
                        break  
        if not lsf_license_dir.files('license*'):
            print "The license file for LSF kit cannot be found."
            pl.info("lsf license file cannot be found.")

    def copyConfDir(self, src_dir, dst_dir):
        if src_dir.exists():
            for s in src_dir.walk():
                dst_path = path(dst_dir) / s.replace(src_dir + '/', '')
                if not dst_path.exists():
                    if s.isdir():
                        dst_path.mkdir()
                        continue
                try:
                    s.copy(dst_path)
                except:
                    pass                    

    def importLSFConfiguration(self, tgzfile):
        lsf_mdir = path('/depot/kusu-migrate/etc/cfm/templates/lsf')
        lsf_dir = path('/etc/cfm/templates/lsf')
        if lsf_dir.exists():
            print "Importing LSF kit configurations and templates..."
            pl.info("import lsf kit configurations to %s" % lsf_dir)
            self.copyConfDir(lsf_mdir, lsf_dir)

        lsf_license_dir = path('/depot/kusu-migrate/opt/lsf/conf')
        lsf_license_list = lsf_license_dir.files('license*')
        if len(lsf_license_list) > 1:
            print "More then one LSF license is found. License is not imported." \
                  "Please find LSF license in /depot/kusu-migrate/opt/lsf/conf/"
            pl.info("more then one lsf license is found in %s. \
                    lsf license is not imported." % tgzfile)
        elif len(lsf_license_list) == 1:
            lsf_license = lsf_license_list[0]
            lsf_license_file = path('/opt/lsf/conf/license.dat')
            if lsf_license.exists():
                if not lsf_license_file.exists():
                    lsf_license.copyfile(lsf_license_file)
                    pl.info("lsf license file in %s file is imported." % tgzfile)
                else:
                    res = raw_input("LSF license was detected in /opt/lsf/conf. "\
                                    "Use LSF license file from %s. (y/n)" % tgzfile)
                    if res.lower() in ['yes','y']:
                        print "Import LSF license file to /opt/lsf/conf/"
                        lsf_license.copyfile(lsf_license_file)
                        pl.info("lsf license file in %s file is imported." % tgzfile)
                    else:
                        print "LSF license is not imported. Please find LSF " \
                              "license in /depot/kusu-migrate/opt/lsf/conf/"
                        pl.info("lsf license is not imported.")

    def _lsf_configuration_exists(self):
        lsf_mdir = path('/depot/kusu-migrate/etc/cfm/templates/lsf')
        if lsf_mdir.exists():
            return True
        return False

    def copyDirectory(self, src_path, dest_path):
        if src_path.exists():
            ddir = dest_path + src_path.dirname()
            if not ddir.exists():
                ddir.makedirs()
            ddir = dest_path + src_path
            src_path.copytree(ddir, symlinks=True)

    def generateMacFiles(self, db, mdir):
        """generate a mac file for each nodegroup in the database"""
        if not mdir.exists():
            mdir.mkdir()
        nodegroups = db.NodeGroups.select()
        for ng in nodegroups:
            nodeslist= self.nodesInfoInNodeGroup(ng)
            if nodeslist:
                f = open(mdir/ng.ngname, 'w')
                f.write("%s" % nodeslist)
                f.close()
                pl.info("mac file for nodegroup %s is generated." % ng.ngname)

    def nodesInfoInNodeGroup(self, ng):
        """get mac, ip, hostname information of the nodes in a nodegroup
           and return as a string"""
        nodes = ng.nodes
        if not nodes:
            return ''
        nodeslist = ''
        for n in nodes:
            for nic in n.nics:
                nodeslist += "%s,\t\t%s,\t\t%s, \n" % (nic.mac, nic.ip, n.name)
        return nodeslist

    def createReportFile(self, report, filename):
        """create a file for report string"""
        if filename.exists():
            filename.remove()
        if report:
            f = open(filename, 'w')
            f.write(report)
            f.close()
            pl.info("PCM configuration report file %s is created." % filename)

    def printGeneratedReport(self):
        """Generate report for current PCM and print on screen"""
        if not self._kusu_version(self.db) == PCM_1_2:
            print "kusu-migrate --report can only be invoked on PCM 1.2"
            sys.exit(1)
        if not self._is_red_hat_distro():
            print "kusu-migrate is only applicable for PCM RHEL edition."
            sys.exit(1)
        print "Generating report..."
        report = self.generateReport(self.db, time.localtime())
        print report

    def generateReport(self, db, time):
        """Get configuration from PCM and return a string of the PCM 
           settings."""
        pl.info("generating configuration report file for current cluster.")
        report = \
"""Summary\n\n\
The following report is a snapshot of your cluster configuration made on 
%s-%s-%s at %s:%s:%s.\nYou may use the information to reinstall your PCM 
cluster. Please refer to the user documentation for more details.\n\n""" % \
(time.tm_year, time.tm_mon, time.tm_mday, \
 time.tm_hour, time.tm_min, time.tm_sec)

        separator = "##############################################################################\n"
        separator1 = "\n============================================================================="

        report += '\n' + separator + "\t\t\tList of Networks:\n" + separator
        stdout, stderr = runCommand('netedit -l')
        report += '\n'+ stdout
        pl.info("network configuration information is retrieved.")

        report += '\n' + separator + "\t\t\tList of Kits:\n" + separator
        stdout, stderr = runCommand('kitops -l')
        report += '\n\n'+ stdout
        pl.info("kits information is retrieved.")

        report += '\n'+ separator + "\t\t\tList of Repositories:\n" + separator
        stdout, stderr = runCommand('repoman -l')
        report += '\n\n'+ stdout
        pl.info("repositories information is retrieved.")

        report += '\n' + separator + "\t\t\tList of Nodegroups:\n" + separator
        nodegroups = db.NodeGroups.select()
        for ng in nodegroups:
            cmd = "ngedit -p '%s'" % ng.ngname
            stdout, stderr = runCommand(cmd)
            report += '\n\n' + stdout
            report += '\nNodes Information for %s: \n\n' % ng.ngname
            report += 'Mac address\t\t\tIP address\t\tHostname\n'
            nodeslist = self.nodesInfoInNodeGroup(ng)
            if nodeslist:
                report += nodeslist
            else:
                report += "<No node records found>\n"
            report += separator1
        pl.info("nodegroups information is retrieved.")

        report += '\n' + separator + "\t\t\tList of custom packages: \n" + separator
        if self.custom_packages_dir.exists() and \
                                         self.custom_packages_dir.listdir():
            for custom_package in self.custom_packages_dir.walk():
                report += custom_package + '\n'
            pl.info("list of custom packages is retrieved.")

        report += '\n' + separator + "\t\t\tList of custom scripts:\n" + separator
        if self.custom_scripts_dir.exists() and \
                                           self.custom_scripts_dir.listdir():
            for custom_script in self.custom_scripts_dir.walk():
                report += custom_script +'\n'
            pl.info("list of custom scripts is retrieved.")

        report += '\n' + separator + "\t\t\tList of post scripts:\n" + separator
        if self.post_scripts_dir.exists() and self.post_scripts_dir.listdir():
            for post_script in self.post_scripts_dir.walk():
                report += post_script + '\n'
            pl.info("list of post scripts is retrieved.")
        pl.info("configuration report for current cluster is generated " \
                "successfully.")
        return report

    def _is_lsf_installed(self, db):
        if db.Kits.selectfirst_by(db.Kits.c.rname.op('ilike')('%'+LSF)):
            return True
        return False

    def _is_red_hat_distro(self):
        if not path('/etc/redhat-release').exists():
            return False
        try:
            f = open('/etc/redhat-release')
            for line in f:
                if 'Red Hat' in line:
                    return True
            return False
        finally:
            f.close()

    def _kusu_version(self, db):
        version = db.AppGlobals.selectfirst_by(kname = KUSU_VERSION_APPGLOBALS_KEY)
        if version:
            return version.kvalue
        try:
            f = open('/etc/kusu-release')
            if PCM_1_2 in f.read():
                return PCM_1_2
            elif PCM_2_0 in f.read():
                return PCM_2_0
        finally:
            f.close()
        print "PCM version cannot be determined."
        sys.exit(1)

    def _exit_if_no_tgzfile_found(self, tgzfile):
        if not path(tgzfile).exists():
            print "The tar-gzipped file %s does not exists." % tgzfile
            sys.exit(1)

    def _exit_if_no_tgzfile_specified(self):
        print "Please provide a tar-gzipped filename with -t option."
        sys.exit(1)

    def _exit_on_invalid_tgzfile_format(self, tgzfile):
        stdout, stderr = runCommand('file %s' % tgzfile)
        if stdout and not 'gzip compressed data' in stdout:
            print "The file <%s> is not a tar-gzipped file format." % tgzfile
            sys.exit(1)

    def _get_appglobals(self, appglobal_key, default_path):
        dpath = default_path
        if appglobal_key:
            try:
                dpath = self.db.AppGlobals.selectfirst_by\
                          (kname = appglobal_key).kvalue
            except AttributeError:
                pass
        return path(dpath)

    def cleanup(self, tdir):
        if tdir.exists():
            tdir.rmtree()

    def printImportPromptMessage(self, tgzfile):
        print """\nThe PCM settings and configurations in the tar-gzipped file, <%s> \n\
will be imported to the directory /depot/kusu-migrate/. Please refer to the user documentation \n\
for more details to reset the PCM configuration with the information in /depot/kusu-migrate/. \n\n\
The following configurations will be handled as stated below if the configurations are found in \n\
the tar-gzipped file:\n\
\t- Platform LSF configurations and license will be imported to /etc/cfm/templates/lsf/ and \n\
\t  /opt/lsf/conf/ respectively.\n\n""" % tgzfile

    def printExportPromptMessage(self, tgzfile):
        print """The PCM settings and configurations have been exported to the tar-gzipped file, <%s>. \n\
Please note that these configurations will not be migrated directly into PCM 2.0. \n\
Invoke kusu-migrate --import -t <%s> to extract these configurations on /depot/kusu-migrate/. \n\
Please refer to the user manual for more information on how to proceed with the re-configuration. \n\n""" \
% (tgzfile, tgzfile)

