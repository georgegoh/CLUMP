#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Framework runner.
#
# Author: George Goh <ggoh@platform.com>
#
# Copyright 2007 Platform Computing Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""This module runs the Text Installer Framework."""
__version__ = "$Revision$"

import logging
from kusu_installer import KusuInstaller

def run():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='kusuinstall.log',
                        filemode='w')

    import kusufactory
    screenFactory = kusufactory.ScreenFactoryImpl
    ks = KusuInstaller(screenFactory, 'Kusu Installer', True)
    ks.run()

if __name__ == '__main__':
    run()
