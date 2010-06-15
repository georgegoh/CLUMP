#!/bin/sh

# Try svn based on first parameter
KUSU_REVISION=`svn info $1 2>/dev/null | grep 'Last Changed Rev:' | awk '{print $4}'`

if [ x$KUSU_REVISION != x ]; then
	echo $KUSU_REVISION
	exit 0
fi

# OK, svn didn't work, let's try git svn
KUSU_REVISION=`git svn find-rev $(git rev-parse HEAD) 2>/dev/null`

# git svn didn't work, let's get a git sha1
if [ x$KUSU_REVISION = x ]; then
	KUSU_REVISION=`git rev-parse HEAD`
fi

echo $KUSU_REVISION
