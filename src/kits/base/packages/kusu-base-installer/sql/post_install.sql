# $Id:$
#
#  Copyright (C) 2007 Platform Computing
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#

# This file contains the fixes and additions needed in the database


# Fix the nodegroup entries
update nodegroups set ngname='compute-imaged' where ngname like('compute-imaged-%') ;
update nodegroups set ngname='compute-diskless' where ngname like('compute-diskless-%') ;
update nodegroups set ngname='installer' where ngname like('installer-%') ;
update nodegroups set ngname='compute' where ngname like('compute-%') and ngname<>'compute-imaged' and ngname<>'compute-diskless' ;

# Assign the correct initrd names 
update nodegroups set initrd='initrd.diskless.3' where ngid=3 ;
update nodegroups set initrd='initrd.diskless.4' where ngid=4 ;

# Setup the modules for the compute-diskless nodes
insert into modules set ngid=4, loadorder=1, module='nfs' ;
insert into modules set ngid=4, loadorder=2, module='ext3' ;
insert into modules set ngid=4, loadorder=3, module='tg3' ;
insert into modules set ngid=4, loadorder=4, module='bnx2' ;
insert into modules set ngid=4, loadorder=5, module='e1000' ;
insert into modules set ngid=4, loadorder=6, module='mii' ;
insert into modules set ngid=4, loadorder=7, module='e100' ;
insert into modules set ngid=4, loadorder=8, module='jbd' ;
insert into modules set ngid=4, loadorder=9, module='lockd' ;
insert into modules set ngid=4, loadorder=10, module='fscache' ;
insert into modules set ngid=4, loadorder=11, module='nfs_acl' ;
insert into modules set ngid=4, loadorder=12, module='sunrpc' ;
insert into modules set ngid=4, loadorder=13, module='mii' ;
insert into modules set ngid=4, loadorder=14, module='pcnet32' ;

# Setup the modules for the compute-imaged nodes
insert into modules set ngid=3, loadorder=1, module='nfs' ;
insert into modules set ngid=3, loadorder=2, module='ext3' ;
insert into modules set ngid=3, loadorder=3, module='bonding' ;
insert into modules set ngid=3, loadorder=4, module='tg3' ;
insert into modules set ngid=3, loadorder=5, module='bnx2' ;
insert into modules set ngid=3, loadorder=6, module='e1000' ;
insert into modules set ngid=3, loadorder=6, module='mptscsih' ;
insert into modules set ngid=3, loadorder=7, module='mptsas' ;
insert into modules set ngid=3, loadorder=8, module='mptfc' ;
insert into modules set ngid=3, loadorder=9, module='mptspi' ;
insert into modules set ngid=3, loadorder=10, module='mptscsi' ;
insert into modules set ngid=3, loadorder=11, module='mptbase' ;
insert into modules set ngid=3, loadorder=12, module='jbd' ;
insert into modules set ngid=3, loadorder=13, module='lockd' ;
insert into modules set ngid=3, loadorder=14, module='fscache' ;
insert into modules set ngid=3, loadorder=15, module='nfs_acl' ;
insert into modules set ngid=3, loadorder=16, module='sunrpc' ;
insert into modules set ngid=3, loadorder=17, module='mii' ;
insert into modules set ngid=3, loadorder=18, module='e100' ;
insert into modules set ngid=3, loadorder=19, module='pcnet32' ;

# Setup the packages for the compute-imaged nodes
insert into packages set ngid=3, packagename='SysVinit' ;
insert into packages set ngid=3, packagename='basesystem' ;
insert into packages set ngid=3, packagename='bash' ;
insert into packages set ngid=3, packagename='redhat-release' ;
insert into packages set ngid=3, packagename='chkconfig' ;
insert into packages set ngid=3, packagename='coreutils' ;
insert into packages set ngid=3, packagename='db4' ;
insert into packages set ngid=3, packagename='e2fsprogs' ;
insert into packages set ngid=3, packagename='filesystem' ;
insert into packages set ngid=3, packagename='findutils' ;
insert into packages set ngid=3, packagename='gawk' ;
insert into packages set ngid=3, packagename='cracklib-dicts' ;
insert into packages set ngid=3, packagename='glibc' ;
insert into packages set ngid=3, packagename='glibc-common' ;
insert into packages set ngid=3, packagename='initscripts' ;
insert into packages set ngid=3, packagename='iproute' ;
insert into packages set ngid=3, packagename='iputils' ;
insert into packages set ngid=3, packagename='krb5-libs' ;
insert into packages set ngid=3, packagename='libacl' ;
insert into packages set ngid=3, packagename='libattr' ;
insert into packages set ngid=3, packagename='libgcc' ;
insert into packages set ngid=3, packagename='libstdc++' ;
insert into packages set ngid=3, packagename='libtermcap' ;
insert into packages set ngid=3, packagename='mingetty' ;
insert into packages set ngid=3, packagename='mktemp' ;
insert into packages set ngid=3, packagename='ncurses' ;
insert into packages set ngid=3, packagename='net-tools' ;
insert into packages set ngid=3, packagename='nfs-utils' ;
insert into packages set ngid=3, packagename='pam' ;
insert into packages set ngid=3, packagename='pcre' ;
insert into packages set ngid=3, packagename='popt' ;
insert into packages set ngid=3, packagename='portmap' ;
insert into packages set ngid=3, packagename='procps' ;
insert into packages set ngid=3, packagename='psmisc' ;
insert into packages set ngid=3, packagename='rdate' ;
insert into packages set ngid=3, packagename='rsh' ;
insert into packages set ngid=3, packagename='rsh-server' ;
insert into packages set ngid=3, packagename='rsync' ;
insert into packages set ngid=3, packagename='sed' ;
insert into packages set ngid=3, packagename='setup' ;
insert into packages set ngid=3, packagename='shadow-utils' ;
insert into packages set ngid=3, packagename='openssh' ;
insert into packages set ngid=3, packagename='openssh-server' ;
insert into packages set ngid=3, packagename='sysklogd' ;
insert into packages set ngid=3, packagename='tcp_wrappers' ;
insert into packages set ngid=3, packagename='termcap' ;
insert into packages set ngid=3, packagename='tzdata' ;
insert into packages set ngid=3, packagename='util-linux' ;
insert into packages set ngid=3, packagename='words' ;
insert into packages set ngid=3, packagename='xinetd' ;
insert into packages set ngid=3, packagename='zlib' ;
insert into packages set ngid=3, packagename='tar' ;
insert into packages set ngid=3, packagename='mkinitrd' ;
insert into packages set ngid=3, packagename='less' ;
insert into packages set ngid=3, packagename='gzip' ;
insert into packages set ngid=3, packagename='which' ;
insert into packages set ngid=3, packagename='util-linux' ;
insert into packages set ngid=3, packagename='module-init-tools' ;
insert into packages set ngid=3, packagename='udev' ;
insert into packages set ngid=3, packagename='cracklib' ;
insert into packages set ngid=3, packagename='component-base-node' ;
  
# Setup the packages for the compute-diskless nodes
insert into packages set ngid=4, packagename='SysVinit' ;
insert into packages set ngid=4, packagename='basesystem' ;
insert into packages set ngid=4, packagename='bash' ;
insert into packages set ngid=4, packagename='redhat-release' ;
insert into packages set ngid=4, packagename='chkconfig' ;
insert into packages set ngid=4, packagename='coreutils' ;
insert into packages set ngid=4, packagename='db4' ;
insert into packages set ngid=4, packagename='e2fsprogs' ;
insert into packages set ngid=4, packagename='filesystem' ;
insert into packages set ngid=4, packagename='findutils' ;
insert into packages set ngid=4, packagename='gawk' ;
insert into packages set ngid=4, packagename='cracklib-dicts' ;
insert into packages set ngid=4, packagename='glibc' ;
insert into packages set ngid=4, packagename='glibc-common' ;
insert into packages set ngid=4, packagename='initscripts' ;
insert into packages set ngid=4, packagename='iproute' ;
insert into packages set ngid=4, packagename='iputils' ;
insert into packages set ngid=4, packagename='krb5-libs' ;
insert into packages set ngid=4, packagename='libacl' ;
insert into packages set ngid=4, packagename='libattr' ;
insert into packages set ngid=4, packagename='libgcc' ;
insert into packages set ngid=4, packagename='libstdc++' ;
insert into packages set ngid=4, packagename='libtermcap' ;
insert into packages set ngid=4, packagename='mingetty' ;
insert into packages set ngid=4, packagename='mktemp' ;
insert into packages set ngid=4, packagename='ncurses' ;
insert into packages set ngid=4, packagename='net-tools' ;
insert into packages set ngid=4, packagename='nfs-utils' ;
insert into packages set ngid=4, packagename='pam' ;
insert into packages set ngid=4, packagename='pcre' ;
insert into packages set ngid=4, packagename='popt' ;
insert into packages set ngid=4, packagename='portmap' ;
insert into packages set ngid=4, packagename='procps' ;
insert into packages set ngid=4, packagename='psmisc' ;
insert into packages set ngid=4, packagename='rdate' ;
insert into packages set ngid=4, packagename='rsh' ;
insert into packages set ngid=4, packagename='rsh-server' ;
insert into packages set ngid=4, packagename='rsync' ;
insert into packages set ngid=4, packagename='sed' ;
insert into packages set ngid=4, packagename='setup' ;
insert into packages set ngid=4, packagename='shadow-utils' ;
insert into packages set ngid=4, packagename='openssh' ;
insert into packages set ngid=4, packagename='openssh-server' ;
insert into packages set ngid=4, packagename='sysklogd' ;
insert into packages set ngid=4, packagename='tcp_wrappers' ;
insert into packages set ngid=4, packagename='termcap' ;
insert into packages set ngid=4, packagename='tzdata' ;
insert into packages set ngid=4, packagename='util-linux' ;
insert into packages set ngid=4, packagename='words' ;
insert into packages set ngid=4, packagename='xinetd' ;
insert into packages set ngid=4, packagename='zlib' ;
insert into packages set ngid=4, packagename='tar' ;
insert into packages set ngid=4, packagename='mkinitrd' ;
insert into packages set ngid=4, packagename='less' ;
insert into packages set ngid=4, packagename='gzip' ;
insert into packages set ngid=4, packagename='which' ;
insert into packages set ngid=4, packagename='util-linux' ;
insert into packages set ngid=4, packagename='module-init-tools' ;
insert into packages set ngid=4, packagename='udev' ;
insert into packages set ngid=4, packagename='cracklib' ;
insert into packages set ngid=4, packagename='component-base-node' ;


# This is for Fedora ONLY!  Fix this in kitops
insert into driverpacks set cid=3, dpname='kernel-2.6.18-1.2798.fc6.i686.rpm', dpdesc='OS Kernel Package' ;