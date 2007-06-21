#!${BASH_EXE}
# $Id$
#
# Kusu specific environment script
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#

wget -m -nH --convert-links --force-html --html-extension --page-requisites http://localhost:8010/
rsync -av --rsh=ssh /data/scratch/buildstatus/* build@ronin:/home/osgdc/www/build/.