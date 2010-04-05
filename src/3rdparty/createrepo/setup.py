#!/usr/bin/env python
#
# $Id: setup.py 1108 2007-06-03 15:29:09Z ltsai $
#

from distutils.core import setup
dist = setup(name="createrepo",
      version="0.4.8",
      platforms=["any"],
      packages=['createrepo'],
      package_dir={'createrepo': 'src'},
      scripts=['src/bin/createrepo', 
               'src/bin/modifyrepo']
 
     )

# Chmod 755 to genpkgmetadata.py in
# lib/<python version>/site-packages/createrepo/
import os
if 'install' in dist.commands:
    path = dist.get_command_obj('install').install_lib

    for file in ['genpkgmetadata.py']:
        os.chmod(os.path.join(path, 'createrepo/' + file), 0755)
        print os.path.join(path, 'createrepo/' + file)
