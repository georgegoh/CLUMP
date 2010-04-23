#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id: uat_helper.py 628 2010-04-22 09:24:10Z ankit $
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

from optparse import Option
from path import path
import ConfigParser

KUSU_UAT_SPEC_DIR = path(os.getenv("KUSU_ROOT", "/opt/kusu")) / 'etc' / 'uat' / 'specs'

class UATPluginBase(object):
    def __init__(self):
        super(UATPluginBase, self).__init__()
        self.status = None

    def pre_check(self):
        pass

    def post_check(self):
        pass

    def run(self, args):
        raise NotImplementedError

    def node_setup(self, node):
        pass

    def node_teardown(self, node):
        pass

    def dump_debug_artifacts(self, artifact_dir):
        pass

    def generate_output_artifacts(self, artifact_dir):
        raise NotImplementedError

class UATHelper(object):
    def generate_file_from_lines(filename, lines):
        """Create `filename' with `lines' as contents.

        If `filename' does not exist, it and any parent directories will be
        created.

        """
        if not filename.dirname().exists():
            filename.dirname().makedirs()
        f = open(filename, 'w')
        f.writelines(lines)
        f.close()
    generate_file_from_lines = staticmethod(generate_file_from_lines)

    @staticmethod
    def get_config_parser(host):
        spec_file = UATHelper.get_file_from_model(UATHelper.get_host_model())
        config = ConfigParser.SafeConfigParser()
        spec_file = KUSU_UAT_SPEC_DIR / spec_file
        config.read(spec_file)
        return config

    @staticmethod     
    def get_host_model():
        return 'example'

    @staticmethod
    def get_file_from_model(model_number, extension='.ini'):
        return model_number + extension

    @staticmethod  
    def read_config(config_parser, section, option, type=''):
        value = None
        try:
            if not type:
                value = config_parser.get(section, option)
            elif type == 'int':
                value = config_parser.getint(section, option)
            elif type == 'float':
                value = config_parser.getfloat(section, option)
            elif type == 'boolean':
                value = config_parser.getboolean(section, option)
        except:
            return value 
        return value

    @staticmethod
    def convert_to_megabytes(number, pattern=''):
        value = None
        try:
            value = float(number)
        except ValueError:
            if number[-1].upper() == 'K':
                value = float(number[:-1]) / 1024
            elif number[-1].upper() == 'M':
                value = float(number[:-1])
            elif number[-1].upper() == 'G': 
                value = float(number[:-1]) * 1024
            elif number[-1].upper == 'T':
                value = float(number[:-1]) * 1024 * 1024
            return value

        if pattern:
            if pattern.upper() == 'K' or pattern.upper() == 'KB':
                value = value / 1024
            elif pattern.upper() == 'G' or pattern.upper() == 'GB':
                value = value * 1024
            elif pattern.upper() == 'T' or pattern.upper() == 'TB':
                value = value * 1024 * 1024
 
        return value

      
class MyOption(Option):
    ACTIONS = Option.ACTIONS + ("extend", )
    STORE_ACTIONS = Option.STORE_ACTIONS + ("extend",)
    TYPED_ACTIONS = Option.TYPED_ACTIONS + ("extend",)
    ALWAYS_TYPED_ACTIONS = Option.ALWAYS_TYPED_ACTIONS + ("extend",)

    def take_action(self, action, dest, opt, value, values, parser):
        if action == "extend":
            lvalue = value.split(",")
            values.ensure_value(dest, []).extend(lvalue)
        else:
            Option.take_action(
                self, action, dest, opt, value, values, parser)

