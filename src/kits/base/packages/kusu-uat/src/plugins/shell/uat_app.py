#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id: uat_app.py 623 2010-04-21 11:36:48Z ankit $
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import os
import sys
import time
import atexit

import kusu.util.log as kusulog

try:
    set
except NameError:
    from sets import Set as set

try:
    import subprocess
except ImportError:
    from popen5 import subprocess

import sqlalchemy as sa
from path import path

from kusu.shell import KusuShellApp
from kusu.uat import UATHelper
from kusu.uat import UATPluginBase
from kusu.uat import UAT_ConfFileError, UAT_PluginNotImplemented

KUSU_SHELL_COMMAND = 'uat'
KUSU_SHELL_COMMAND_CLASS = 'UATApp'

KUSU_UAT_PLUGIN_DIR = path(os.getenv("KUSU_ROOT", "/opt/kusu")) / 'lib' / 'plugins' / 'uat'
KUSU_UAT_CONF_DIR = path(os.getenv("KUSU_ROOT", "/opt/kusu")) / 'etc' / 'uat' / 'conf.d'
KUSU_UAT_ARTIFACT_ROOT = path(os.getenv("KUSU_ROOT", "/opt/kusu")) / 'var' / 'uat'

usage = """usage: uat [options] [all | check] [,check ...]"""
version = """uat version ${VERSION_STR}"""

def create_dir(dir):
    try:
        path(dir).makedirs()
    except OSError:
        pass

class UATApp(KusuShellApp):
    """Runs UAT plugins on appropriate nodes.

    At the heart of this class are the dictionaries _nodegroups_by_type,
    _nodes_by_nodegroup and _nodegroups_by_component. They provide a means of
    obtaining a list of all nodes in a nodegroup based on the nodegroup's name,
    type, or the assumed presence of a component.

    _nodegroups_by_type is keyed by nodegroup type (compute, installer, etc)
    and the value is a list of nodegroups which share that type.

    _nodegroups_by_component is keyed by component, with the value being a list
    of nodegroups having said component associated.

    _nodes_by_nodegroup is keyed by nodegroup name and contains lists of node
    names for nodes belonging in said nodegroup.

    This allows us to determine a list of nodes based on nodegroup:

        nodes = _nodes_by_nodegroup[nodegroup.name]

    as well as based on a nodegroup type:

        nodes = []
        nodegroups = _nodegroups_by_type[type]
        for nodegroup in nodegroups:
            nodes.extend(_nodes_by_nodegroup[nodegroup])

    or the presence of a component:

        nodes = []
        nodegroups = _nodegroups_by_component[component]
        for nodegroup in nodegroups:
            nodes.extend(_nodes_by_nodegroup[nodegroup])

    Each check plugin can specify restrictions such as "I only run on compute
    nodegroups" or "I require component-nagios-monitored-node to be installed"
    and thus narrow down the list of nodes the check applies to.
    """
    def __init__(self, args, db=None, **kwargs):
        super(UATApp, self).__init__(args, db, **kwargs)

        if not self._remaining_args:
            raise ValueError, "'%s' called with no arguments" % args[0]

        self._supplied_commands = self._remaining_args[0].split(',')
        self._plugin_dir = KUSU_UAT_PLUGIN_DIR
        self._conf_dir = KUSU_UAT_CONF_DIR
        self._now = time.localtime()
        self._artifact_root = path(KUSU_UAT_ARTIFACT_ROOT) / self._generate_date_time()
        create_dir(self._artifact_root)
        self._nodegroups_by_type = {}
        self._nodes_by_nodegroup = {}
        self._nodegroups_by_component = {}
        self._summary_lines = []
        self.check_dict = {}
        self.command_dict = {}
        self.command_status = {}
        self._logger = kusulog.getKusuLog()
        self._logger.addFileHandler('/var/log/kusu/kusuUAT.log')
        sys.path.append(self._plugin_dir)

    def _generate_date_time(self):
        return time.strftime("%Y-%m-%d_%H-%M-%S", self._now)

    def _configure_options(self):
        parser = super(UATApp, self)._configure_options(usage=usage, version=version)

        parser.add_option('-n', '--nodes', help='Comma-separated list of nodes to check')
        parser.add_option('-g', '--nodegroups', help='Comma-separated list of nodegroups whose nodes to check')

        return parser

    def run(self):
        commands = {}
        self._needs_database()
        configured_checks = self._read_config_files()
        self._populate_dictionaries(configured_checks)
        if self._supplied_commands == ['all']:
            self._supplied_commands = configured_checks.keys()

        disqualified_checks = []
        for check_name in self.check_dict.keys():
            if check_name not in self._supplied_commands:
                continue
            try:
                commands = self._get_command_list_for_check(check_name)
            except UAT_ConfFileError, msg:
                self._err.write('Configuration file error: %s.\n' % msg)
                sys.exit(1)
            if commands:
                self.command_dict[check_name] = commands
            else:
                disqualified_checks.append(check_name)
            commands = {}

        self._emit_output(self._get_header(self.command_dict) + '\n')
        self._emit_output("UAT found no nodes for %d checks (%s)\n" %(len(disqualified_checks), ', '.join(disqualified_checks)))

        for check_name in self.command_dict.keys():
            self._run_check(check_name)

        self._generate_summary()
        self._create_link_to_artifact_dir()

    def _read_config_files(self):
        try:
            checks = {}
            for f in self._conf_dir.files():
                ns = {}
                execfile(f, ns)
                checks.update(ns.get('checks', {}))
            return checks
        except SyntaxError, e:
            raise RuntimeError, "%s in %s (line %s, col %s)" % (e.msg, e.filename, e.lineno, e.offset)

    def _populate_dictionaries(self, configured_checks):
        """Fill nodegroup, node and check dictionaries with data"""
        relevant_ngids = self._populate_nodes_by_nodegroup()
        self._populate_nodegroups_by_type(relevant_ngids)
        self._populate_nodegroups_by_component(relevant_ngids)
        self._populate_check_dict(configured_checks)

    def _populate_nodes_by_nodegroup(self):
        supplied_nodes = supplied_nodegroups = None
        if self._options.nodes is not None:
            supplied_nodes = self._options.nodes.split(",")
        if self._options.nodegroups is not None:
            supplied_nodegroups = self._options.nodegroups.split(",")

        stmt = sa.select([self._db.NodeGroups.c.ngid, self._db.NodeGroups.c.ngname, self._db.Nodes.c.name],
                         whereclause=self._db.Nodes.c.ngid==self._db.NodeGroups.c.ngid)
        if supplied_nodes and supplied_nodegroups:
            stmt.append_whereclause(sa.or_(self._db.Nodes.c.name.in_(*supplied_nodes),
                                           self._db.NodeGroups.c.ngname.in_(*supplied_nodegroups)))
        elif supplied_nodes:
            stmt.append_whereclause(self._db.Nodes.c.name.in_(*supplied_nodes))
        elif supplied_nodegroups:
            stmt.append_whereclause(self._db.NodeGroups.c.ngname.in_(*supplied_nodegroups))

        stmt.order_by(self._db.NodeGroups.c.ngname, self._db.Nodes.c.name)
        results = stmt.execute().fetchall()
        for record in results:
            ng_name = record['ngname']
            node_name = record['name']
            if ng_name not in self._nodes_by_nodegroup:
                self._nodes_by_nodegroup[ng_name] = []
            self._nodes_by_nodegroup[ng_name].append(node_name)
        return set([x['ngid'] for x in results])

    def _populate_nodegroups_by_type(self, relevant_ngids):
        stmt = sa.select([self._db.NodeGroups.c.type, self._db.NodeGroups.c.ngname],
                         whereclause=self._db.NodeGroups.c.ngid.in_(*relevant_ngids))
        results = stmt.execute().fetchall()
        for record in results:
            ng_type = record['type']
            ng_name = record['ngname']
            if ng_type not in self._nodegroups_by_type:
                self._nodegroups_by_type[ng_type] = []
            self._nodegroups_by_type[ng_type].append(ng_name)

    def _populate_nodegroups_by_component(self, relevant_ngids):
        stmt = sa.select([self._db.Components.c.cname, self._db.NodeGroups.c.ngname],
                         whereclause=sa.and_(self._db.NodeGroups.c.ngid==self._db.NGHasComp.c.ngid,
                                             self._db.NGHasComp.c.cid==self._db.Components.c.cid,
                                             self._db.NodeGroups.c.ngid.in_(*relevant_ngids)))
        results = stmt.execute().fetchall()
        for record in results:
            component_name = record['cname']
            ng_name = record['ngname']
            if component_name not in self._nodegroups_by_component:
                self._nodegroups_by_component[component_name] = []
            self._nodegroups_by_component[component_name].append(ng_name)

    def _populate_check_dict(self, configured_checks):
        for check_name, check_attributes in configured_checks.iteritems():
            self.check_dict[check_name] = {}
            for key, values in check_attributes.iteritems():
                self.check_dict[check_name][key] = values

    def _get_valid_nodes_by_nodegroup_type(self, types):
        valid_nodegroups = set()
        for type in types:
            if type in self._nodegroups_by_type:
                valid_nodegroups.update(self._nodegroups_by_type[type])
        return self._get_valid_nodes_by_nodegroup(valid_nodegroups)

    def _get_valid_nodes_by_nodegroup(self, valid_nodegroups):
        valid_nodes = set()
        for valid_nodegroup in valid_nodegroups:
            if valid_nodegroup in self._nodes_by_nodegroup:
                valid_nodes.update(self._nodes_by_nodegroup[valid_nodegroup])
        return valid_nodes

    def _get_valid_nodes_by_component(self, components):
        valid_nodegroups = set()
        for component in components:
            if component in self._nodegroups_by_component:
                valid_nodegroups.update(self._nodegroups_by_component[component])
        return self._get_valid_nodes_by_nodegroup(valid_nodegroups)

    def _run_check(self, check_name):
        command_list = []
        self.plugin_inst_dict = {}
        print "\nRunning %s Check" %check_name
        self._logger.info("Running %s Check" %check_name)
        plugin_list = [cmd.split()[0] for cmd in self.check_dict[check_name]['commands']]

        try:
            self._populate_plugin_inst(plugin_list, check_name)
        except UAT_PluginNotImplemented, msg:
            self._register_failure(check_name, self.command_dict[check_name].keys())
            self._logger.error("Check %s failed to run because %s" % (check_name, msg))
            self._emit_output("\tFail: Check %s failed to run because %s.\n" % (check_name, msg))
            return

        try:
            self._check_pre(check_name)
        except Exception, e:
            self._register_failure(check_name, self.command_dict[check_name].keys())
            self._logger.error("Check %s failed, 'pre_check' hook for the plugin %s has raised the exception: %s " % (check_name, plugin, e))
            self._emit_output("\tFail: Check %s failed, 'pre_check' hook for the plugin %s has raised the exception: %s \n" % (check_name, plugin, e))
            return

        self._run_check_for_all_nodes(check_name)

        self._check_post(plugin_list)

    def _populate_plugin_inst(self, plugin_list, check_name):
        for plugin in plugin_list:
            plugin_class = self._get_plugin_class(plugin)
            if 'init_args' in self.check_dict[check_name]:
                self.check_dict[check_name]['init_args']['logger'] = self._logger
                self.check_dict[check_name]['init_args']['db'] = self._db
                self.plugin_inst_dict[plugin] = plugin_class(self.check_dict[check_name]['init_args'])
            else:
                self.plugin_inst_dict[plugin] = plugin_class({'logger': self._logger, 'db': self._db})

    def _check_pre(self, check_name):
        for plugin, plugin_inst in self.plugin_inst_dict.iteritems():
            plugin_inst.pre_check()
            atexit.register(plugin_inst.post_check)

    def _run_check_for_all_nodes(self, check_name):
        for node, command_list in self.command_dict[check_name].iteritems():
            set_skip = 0
            for cmd in command_list:
                plugin_inst = self.plugin_inst_dict[cmd['plugin']]
                self._emit_output('\t%s %s: ' % (cmd['plugin'], node))
                if set_skip == 1:
                    self._logger.info("Skipped plugin '%s' for node '%s' " % (cmd['plugin'], node))
                    self._emit_output('Skipped\n')
                    continue
                try:
                    set_skip = self._run_check_for_node(check_name, plugin_inst, node, cmd)
                finally:
                    self.plugin_inst_dict[cmd['plugin']].node_teardown(node)

                self._out.flush() # no newline above & result may take a while

    def _run_check_for_node(self, check_name, plugin_inst, node, cmd):
        try:
            plugin_inst.node_setup(node)
        except Exception, msg:
            set_skip = 1
            self._register_failure(check_name, [node])
            self._logger.error("Check %s failed for node %s with exception: %s" % (check_name, node, msg))
            self._emit_output("Check %s failed for node %s with exception: %s" % (check_name, node, msg))
        else:
            set_skip = self._run_plugin_for_node(check_name, plugin_inst, node, cmd)

        try:
           plugin_inst.generate_output_artifacts(self._artifact_root / check_name)
        except Exception, msg:
            self._emit_output('\t\tPlugin %s failed to generate output: %s\n' % (cmd['plugin'], msg))

        return set_skip

    def _run_plugin_for_node(self, check_name, plugin_inst, node, cmd):
        try:
            returncode, status_msg = plugin_inst.run(cmd['cmd'])
        except Exception, msg:
            self._register_failure(check_name, [node])
            self._emit_output('FAIL - %s\n' % msg)
            self._logger.error("Check '%s' failed for node '%s' while performing test'%s': %s" %(check_name, node, " ".join(cmd['cmd']), msg))
            return 1

        if not returncode:
            self._emit_output('OK - %s\n' % status_msg)
            return returncode

        self._register_failure(check_name, [node])
        plugin_inst.dump_debug_artifacts(self._artifact_root / check_name)
        self._emit_output('FAIL - %s\n' % status_msg)
        self._logger.error("Check '%s' failed for node '%s' while performing test'%s'." %(check_name, node, " ".join(cmd['cmd'])))

        return 1

    def _register_failure(self, check_name, nodes):
       for node in nodes:
           if check_name in self.command_status:
               self.command_status[check_name].append(node)
           else:
               self.command_status[check_name] = [node]

    def _check_post(self, plugin_list):
        # Teardown: LIFO, last plugin setup will be teardown the first.
        plugin_list.reverse()
        for plugin in plugin_list:
            self.plugin_inst_dict[plugin].post_check()
            try:
                atexit._exithandlers.remove((self.plugin_inst_dict[plugin].post_check, (), {}))
            except ValueError:
                continue

    def _get_plugin_class(self, plugin_name):
        plugin_file = self._plugin_dir / plugin_name + '.py'
        if plugin_file.isfile():
            plugin_module = __import__(plugin_name, globals(), locals(), [])
            for attribute in dir(plugin_module):
                module_attribute = getattr(plugin_module, attribute)
                if type(module_attribute) == type and issubclass(module_attribute, UATPluginBase) and attribute != 'UATPluginBase':
                    return module_attribute

        raise UAT_PluginNotImplemented, 'Plugin %s not implemented' % plugin_name

    def _get_command_list_for_check(self, check_name):
        command_dict = {}
        node_list = set()
        for nodes in self._nodes_by_nodegroup.values():
            node_list.update(nodes)
        check = self.check_dict[check_name]
        nodes_by_nodegroup_type = nodes_by_component = set(node_list)
        if 'nodegroup_types' in check:
            nodes_by_nodegroup_type = self._get_valid_nodes_by_nodegroup_type(check['nodegroup_types'])
        if 'components' in check:
            nodes_by_component = self._get_valid_nodes_by_component(check['components'])
        valid_nodes = nodes_by_nodegroup_type.intersection(nodes_by_component)

        if 'commands' in check and type(check['commands']) == list and check['commands']:
            for node in valid_nodes:
                command_list = self._generate_check_commands_for_node(check_name, check['commands'], node)
                if command_list:
                    command_dict[node] = command_list
        else:
            raise UAT_ConfFileError, 'Syntax error in the commands list of %s check' % check_name   

        return command_dict

    def _generate_check_commands_for_node(self, check_name, check_commands, node):
        commands = []
        for command in check_commands:
            cmd = {}
            args = (command % {'node_name': node}).split()
            cmd['cmd'] = args
            cmd['check_name'] = check_name
            cmd['plugin'] = args[0]
            commands.append(cmd)

        return commands

    def _emit_output(self, message):
        # In the future, if/when a -q/--quiet flag is implemented, we can skip
        # writing to self._out.
        self._out.write(message)
        self._summary_lines.append(message)

    def _get_header(self, commands):
        ## TO DO: Need to extend this Function
        num_commands = 0
        num_checks = 0
        node_list = []
        for check_name, values in commands.iteritems():
            num_checks += 1
            for node, command_list in values.iteritems():
                num_commands += len(command_list)
                node_list.append(node)

        date = time.strftime("%Y-%m-%d %H:%M:%S", self._now)
        header = "UAT %s running " % date
        if num_checks == 1:
            header += "%d check (%d command(s) " % (num_checks, num_commands)
        else:
            header += "%d checks (%d commands " % (num_checks, num_commands)
        num_nodes = len(set(node_list))
        if num_nodes == 1:
            header += "on %d node)" % num_nodes
        else:
            header += "on %d nodes)" % num_nodes
        return header

    def print_result(self):
        self._emit_output("Done!\n")

    def _generate_summary(self):
        if self.command_status.keys():
            print("\n%d Check(s) failed" % len(self.command_status.keys()))
        else:
            print("\nUAT ran Successfully. No failures were reported.")

        for check_name, node_list in self.command_status.iteritems():
            print("\tFailure: %s failed on node(s): %s" % (check_name, str(node_list)[1:-1]))

    def generate_output_artifacts(self):
        UATHelper.generate_file_from_lines(self._artifact_root / 'summary.txt', self._summary_lines)

    def _create_link_to_artifact_dir(self):
        if path(KUSU_UAT_ARTIFACT_ROOT / 'lastrun').islink():
            path(KUSU_UAT_ARTIFACT_ROOT / 'lastrun').unlink()

        self._artifact_root.symlink(KUSU_UAT_ARTIFACT_ROOT / 'lastrun')
        print "\nUAT artifacts are stored at: %s " % (KUSU_UAT_ARTIFACT_ROOT / 'lastrun')
