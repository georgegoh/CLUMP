#!/bin/sh
# In Kusu Installer mode?
# Do not change the following line!
if [ -e /tmp/kusu/installer_running ]; then exit 0; fi 

# Put any custom stuff after this line
# SQL/Shell/Python code to update the database.. The updates may optionally
# include Node group creation and component association

# sqlrunner may be used to perform sql injections
# ngedit may be used non-interactively to add and copy nodegroups
