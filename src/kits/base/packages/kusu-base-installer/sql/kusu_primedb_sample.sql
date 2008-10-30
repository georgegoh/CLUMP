# $Id$
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


# Setup a default repo and kits
insert into repos values (1, "Fedora_6", "/depot/repos/1", "installer00", 'fedora-6-i386') ;
insert into repos values (2, "Special RHEL 5 for Diskless nodes", "/depot/repos/2", "installer0", 'rhel-5.1-i386') ;
insert into repos values (3, "Fedora_7", "/depot/repos/3", "installer00", 'fedora-7-x86_64') ;

insert into kits values (1, "Fedora 6", "fedora-6-i386", "6.0", 1, 0, "i386") ;
insert into kits values (2, "RHEL 5.1", "Redhat Enterprise Linux 5", "5.1", 1, 0, "i386") ;
insert into kits values (3, "Base", "Kusu Base", "5.1", 0, 0, "i386") ;
insert into kits values (4, "LSF", "LSF 7.0 EP2", "7.2", 0, 1, "i386") ;
insert into kits values (5, "OFED", "OpenFabric Infiniband Drivers", "5.1", 0, 1, "i386") ;
insert into kits values (6, "MPI", "OpenMPI and others", "5.1", 0, 1, "i386") ;
insert into kits values (7, "Base", "Kusu Base", "5.1", 0, 0, "x86_64") ;
insert into kits values (8, "Fedora 7", "fedora-7-x86_64", "7.0", 1, 0, "x86_64") ;
insert into kits values (9, 'DVendor', 'dvendor', "5.1", 0, 0, "x86_64") ;

insert into repos_have_kits values (1, 1) ;
insert into repos_have_kits values (1, 3) ;
insert into repos_have_kits values (1, 4) ;
insert into repos_have_kits values (1, 5) ;
insert into repos_have_kits values (1, 6) ;
insert into repos_have_kits values (2, 2) ;
insert into repos_have_kits values (2, 3) ;
insert into repos_have_kits values (3, 8) ;
insert into repos_have_kits values (3, 9) ;

# Setup some node groups
insert into nodegroups values (1,1,'Installer', 'package', 'Default Installer Node group', 'installer#NN', 'vmlinuz-2.1.18-1.2798.fc6.i386', 'initrd-2.6.18-1.2798.fc6.img.i386', 'ro root=/dev/VolGroup00/LogVol00 rhgb quiet', 'installer') ;

insert into nodegroups values (2,1,'Compute', 'package', 'Default Compute Node group', 'node#NNNN', 'vmlinuz-2.1.18-1.2798.fc6.i386', 'initrd-2.6.18-1.2798.fc6.img.i386', 'Test kernel args in grub.conf for Compute', 'compute') ;

insert into nodegroups values (3,1,'Compute Diskless', 'diskless', 'Default Diskless Compute Node group', 'host#NNN', 'vmlinuz-2.1.18-1.2798.fc6.i386', 'Fedora_6.img.i386', 'Test kernel args in grub.conf for diskless Compute', 'compute') ;

insert into nodegroups values (4,1,'Compute Disked', 'disked', 'Default Disked Imaged Compute Node group', 'c#RR-#NN', 'vmlinuz-2.1.18-1.2798.fc6.i386', 'Fedora_6.img.i386', 'Test kernel args in grub.conf for disked Compute', 'compute') ;

insert into nodegroups values (5,1,'test', 'diskless', 'Test image for dependency checks', 'c#RR-#NN', 'vmlinuz', 'Fedora_6.img.i386', 'Test', 'compute') ;

insert into nodegroups values (6,3,'Fedora 7 Installer', 'package', 'Fedora 7 Installer Node group', 'installer#NN', 'vmlinuz-2.6.20-1.3003.fc7', 'Fedora_7.img.x86_64', 'ro root=/dev/VolGroup00/LogVol00 rhgb quiet', 'installer') ;

insert into nodegroups values (7,3,'Fedora 7 Compute', 'diskless', 'Fedora 7 Diskless Node group', 'host-diskless-#NNNN', 'vmlinuz-2.6.20-1.3003.fc7', 'Fedora_7.img.x86_64', 'Test kernel args in grub.conf for Fedora 7 diskless Compute', 'compute') ;

# Setup the nodes entries for the installer
insert into nodes values (1,1,'installer00', NULL, NULL, NULL, 'Installed', 1, '2007/1/1 2:22:22', 0, 0) ;

# Setup the nodes entries for some compute nodes
insert into nodes values (2,2,'node0000', NULL, NULL, 'ro root=LABEL=/1 rhgb quiet', 'Installed', 1, '2007/1/1 11:11:11', 0, 0) ;
insert into nodes values (3,2,'node0001', NULL, NULL, NULL, 'Installed', 1, '2007/1/1 11:11:11', 0, 1) ;
insert into nodes values (4,2,'node0002', NULL, NULL, NULL, 'Installed', 1, '2007/1/1 11:11:11', 0, 2) ;
insert into nodes values (5,2,'node0003', NULL, NULL, NULL, 'Expired', 0, '2007/1/1 11:11:11', 0, 3) ;
insert into nodes values (6,2,'node0004', NULL, NULL, NULL, 'Expired', 0, '2007/1/1 11:11:11', 0, 4) ;

insert into nodes values (7,3,'host000', NULL, NULL, 'mem=512', 'Installed', 0, '2007/1/1 11:11:11', 0, 0) ;
insert into nodes values (8,3,'host001', NULL, NULL, NULL, 'Installed', 0, '2007/1/1 11:11:11', 0, 1) ;
insert into nodes values (9,3,'host002', NULL, NULL, NULL, 'Installed', 0, '2007/1/1 11:11:11', 0, 2) ;
insert into nodes values (10,3,'host003', 'vmlinuz-2.6.15-1.2054_FC5', 'initrd-2.6.15-1.2054_FC5.img' , 'ro root=LABEL=/1 rhgb quiet', 'Expired', 0, '2007/1/1 11:11:11', 0, 3) ;
insert into nodes values (11,3,'host004', NULL, NULL, NULL, 'Expired', 0, '2007/1/1 11:11:11', 0, 4) ;

insert into nodes values (12,4,'c01-00', NULL, NULL, NULL, 'Installed', 1, '2007/1/1 11:11:11', 1, 0) ;
insert into nodes values (13,4,'c01-01', NULL, NULL, NULL, 'Installed', 1, '2007/1/1 11:11:11', 1, 0) ;
insert into nodes values (14,4,'c02-00', NULL, NULL, NULL, 'Installed', 1, '2007/1/1 11:11:11', 2, 0) ;
insert into nodes values (15,4,'c02-01', NULL, NULL, NULL, 'Expired', 0, '2007/1/1 11:11:11', 2, 1) ;
insert into nodes values (16,4,'c02-02', NULL, NULL, NULL, 'Expired', 0, '2007/1/1 11:11:11', 2, 2) ;

# Setup the nodes entries for the secondary installers
insert into nodes values (17,1,'installer01', NULL, NULL, NULL, 'Installed', 1, '2007/1/1 2:22:22', 0, 1) ;
insert into nodes values (18,1,'installer02', NULL, NULL, NULL, 'Installed', 1, '2007/1/1 2:22:22', 0, 2) ;

# Setup the default partitioning scheme for default installer nodes
insert into partitions values (1,1,'1', '1', '/boot', 'ext3', '100', '', 0) ;
insert into partitions values (2,1,'1', '2', '', 'physical volume', '200000', 'fill;pv;vg=VolGroup00', 0) ;		
insert into partitions values (3,1,'VolGroup00', '', '', '', '', 'vg;extent=32M', 0) ;
insert into partitions values (4,1,'', '', '', 'linux-swap', '1000', 'lv;vg=VolGroup00', 0) ;
insert into partitions values (5,1,'', '', '/export', 'ext3', '20000', 'lv;vg=VolGroup00', 0) ;
insert into partitions values (6,1,'', '', '/depot', 'ext3', '40000', 'fill;lv;vg=VolGroup00', 0) ;

# Setup the default partitioning scheme for default package based compute nodes
insert into partitions values (7,2,'1', '1', '/boot', 'ext3', '100', '', 0) ;
insert into partitions values (8,2,'1', '2', '', 'physical volume', '10000', 'fill;pv;vg=VolGroup00', 0) ;	
insert into partitions values (9,2,'VolGroup00', '', '', '', '', 'vg;extent=32M', 0) ;	
insert into partitions values (10,2,'',  '',  '/', 'ext3', '5000',  'lv;vg=VolGroup00', 0) ;
insert into partitions values (11,2,'',  '', '', 'linux-swap', '1000',  'lv;vg=VolGroup00', 0) ;
insert into partitions values (12,2,'',  '',  '/scratch', 'ext3', '4000',  'fill;lv;vg=VolGroup00', 0) ;

# Setup the default partitioning scheme for default package based compute nodes
insert into partitions values (13,4,'1', '1', '/boot', 'ext3', '100', '', 0) ;
insert into partitions values (14,4,'1', '2', '', 'physical volume', '10000', 'fill;pv;vg=VolGroup00', 0) ;	
insert into partitions values (15,4,'VolGroup00', '', '', '', '', 'vg;extent=32M', 0) ;	
insert into partitions values (16,4,'',  '',  '/', 'ext3', '9000',  'fill;lv;vg=VolGroup00', 0) ;
insert into partitions values (17,4,'',  '', '', 'linux-swap', '1000',  'lv;vg=VolGroup00', 0) ;


# Setup a few default networks.  This would be set by the Kusu installer.
insert into networks values (1, '172.25.243.0', '255.255.255.0', 'eth1', '', '172.25.243.2','','Installer public network.  Set by Installer', '172.25.243.200', 'public', 1,0) ;
insert into networks values (2, '10.0.0.0', '255.0.0.0', 'eth0', '-eth0', '10.1.1.1','My Options','Installer private network.  Set by Installer', '10.1.2.0', 'provision', 1,0) ;
insert into networks values (3, '20.2.0.0', '255.255.0.0', 'ib0', '-ib0', '20.2.1.1','','Installer private network.  Set by Installer', '20.2.2.0', 'provision', 1,0) ;
insert into networks values (4, '10.0.0.0', '255.0.0.0', 'vmnet1', '-vmnet1', '10.0.0.1','','Installer private network.  Set by Installer', '10.10.2.0', 'provision', 1,0) ;

# Setup the relationship between the networks and the node groups.  (idnet, ngid, netid)
insert into ng_has_net values (1,1) ;
insert into ng_has_net values (1,4) ;
insert into ng_has_net values (2,1) ;
insert into ng_has_net values (2,2) ;
insert into ng_has_net values (2,3) ;
insert into ng_has_net values (3,2) ;
insert into ng_has_net values (4,2) ;
insert into ng_has_net values (4,3) ;
insert into ng_has_net values (5,2) ;
insert into ng_has_net values (5,3) ;
insert into ng_has_net values (6,1) ;
insert into ng_has_net values (6,2) ;
insert into ng_has_net values (7,2) ;
insert into ng_has_net values (17,1) ;
insert into ng_has_net values (17,2) ;
insert into ng_has_net values (18,1) ;
insert into ng_has_net values (18,2) ;

# Setup the nics table for the Installer node
insert into nics values (32, 1, 1, '00:11:22:33:44:55', '172.25.243.1', 1) ;
insert into nics values (1, 1, 2, NULL, '10.1.0.1', 0) ;
# Setup the nics table for the other Installer nodes
insert into nics values (33, 17, 1, '10:11:22:33:44:55', '172.25.243.2', 1) ;
insert into nics values (34, 17, 2, NULL, '10.1.0.2', 0) ;
insert into nics values (35, 18, 1, '20:11:22:33:44:55', '172.25.243.3', 1) ;
insert into nics values (36, 18, 2, NULL, '10.1.0.3', 0) ;
# For the nodes in the Compute node group.  Each has 3 NICs
insert into nics values (2, 2, 1, '00:11:22:33:44:00', '172.25.243.200', 1) ;
insert into nics values (3, 2, 2, NULL, '10.1.2.0', 0) ;
insert into nics values (4, 2, 3, NULL, '10.2.2.0', 0) ;
insert into nics values (5, 3, 1, '00:11:22:33:44:10', '172.25.243.201', 1) ;
insert into nics values (6, 3, 2, NULL, '10.1.2.1', 0) ;
insert into nics values (7, 3, 3, NULL, '10.2.2.1', 0) ;
insert into nics values (8, 4, 1, '00:11:22:33:44:20', '172.25.243.202', 1) ;
insert into nics values (9, 4, 2, NULL, '10.1.2.2', 0) ;
insert into nics values (10, 4, 3, NULL, '10.2.2.2', 0) ;
insert into nics values (11, 5, 1, '00:11:22:33:44:30', '172.25.243.203', 1) ;
insert into nics values (12, 5, 2, NULL, '10.1.2.3', 0) ;
insert into nics values (13, 5, 3, NULL, '10.2.2.3', 0) ;
insert into nics values (14, 6, 1, '00:11:22:33:44:40', '172.25.243.204', 1) ;
insert into nics values (15, 6, 2, NULL, '10.1.2.4', 0) ;
insert into nics values (16, 6, 3, NULL, '10.2.2.4', 0) ;
# For the nodes in the Compute Diskless node group.  Each has 1 NICs
insert into nics values (17, 7, 2, '00:0c:29:84:e9:0e', '10.1.2.5', 1) ;
insert into nics values (18, 8, 2, '20:11:ff:33:44:41', '10.1.2.6', 1) ;
insert into nics values (19, 9, 2, '30:11:ff:33:44:41', '10.1.2.7', 1) ;
insert into nics values (20, 10, 2, '40:11:ff:33:44:41', '10.1.2.8', 1) ;
insert into nics values (21, 11, 2, '50:11:ff:33:44:41', '10.1.2.9', 1) ;
# For the nodes in the Compute Disked node group.  Each has 2 NICs
insert into nics values (22, 12, 2, '10:31:aa:33:44:40', '10.1.2.10', 1) ;
insert into nics values (23, 12, 3, NULL, '10.2.2.5', 0) ;
insert into nics values (24, 13, 2, '10:31:aa:33:44:41', '10.1.2.11', 1) ;
insert into nics values (25, 13, 3, NULL, '10.2.2.6', 0) ;
insert into nics values (26, 14, 2, '10:31:aa:33:44:42', '10.1.2.12', 1) ;
insert into nics values (27, 14, 3, NULL, '10.2.2.7', 0) ;
insert into nics values (28, 15, 2, '10:31:aa:33:44:43', '10.1.2.13', 1) ;
insert into nics values (29, 15, 3, NULL, '10.2.2.8', 0) ;
insert into nics values (30, 16, 2, '10:31:aa:33:44:44', '10.1.2.14', 1) ;
insert into nics values (31, 16, 3, NULL, '10.2.2.9', 0) ;

# Setup the packages for the diskless compute nodes
insert into packages values (1,3,'SysVinit') ;
insert into packages values (2,3,'basesystem') ;
insert into packages values (3,3,'bash') ;
insert into packages values (4,3,'redhat-release') ;
insert into packages values (5,3,'chkconfig') ;
insert into packages values (6,3,'coreutils') ;
insert into packages values (7,3,'db4') ;
insert into packages values (8,3,'e2fsprogs') ;
insert into packages values (9,3,'filesystem') ;
insert into packages values (10,3,'findutils') ;
insert into packages values (11,3,'gawk') ;
#insert into packages values (12,3,'glib') ;
insert into packages values (13,3,'glibc') ;
insert into packages values (14,3,'glibc-common') ;
insert into packages values (15,3,'initscripts') ;
insert into packages values (16,3,'iproute') ;
insert into packages values (17,3,'iputils') ;
insert into packages values (18,3,'krb5-libs') ;
insert into packages values (19,3,'libacl') ;
insert into packages values (20,3,'libattr') ;
insert into packages values (21,3,'libgcc') ;
insert into packages values (22,3,'libstdc++') ;
insert into packages values (23,3,'libtermcap') ;
insert into packages values (24,3,'mingetty') ;
insert into packages values (25,3,'mktemp') ;
insert into packages values (26,3,'ncurses') ;
insert into packages values (27,3,'net-tools') ;
insert into packages values (28,3,'nfs-utils') ;
insert into packages values (29,3,'pam') ;
insert into packages values (30,3,'pcre') ;
insert into packages values (31,3,'popt') ;
insert into packages values (32,3,'portmap') ;
insert into packages values (33,3,'procps') ;
insert into packages values (34,3,'psmisc') ;
insert into packages values (35,3,'rdate') ;
insert into packages values (36,3,'rsh') ;
insert into packages values (37,3,'rsh-server') ;
insert into packages values (38,3,'rsync') ;
insert into packages values (39,3,'sed') ;
insert into packages values (40,3,'setup') ;
insert into packages values (41,3,'shadow-utils') ;
insert into packages values (42,3,'openssh') ;
insert into packages values (43,3,'openssh-server') ;
insert into packages values (44,3,'sysklogd') ;
insert into packages values (45,3,'tcp_wrappers') ;
insert into packages values (46,3,'termcap') ;
insert into packages values (47,3,'tzdata') ;
insert into packages values (48,3,'util-linux') ;
insert into packages values (49,3,'words') ;
insert into packages values (50,3,'xinetd') ;
insert into packages values (51,3,'zlib') ;
insert into packages values (52,3,'tar') ;
insert into packages values (53,3,'mkinitrd') ;
insert into packages values (54,3,'less') ;
insert into packages values (55,3,'gzip') ;
insert into packages values (56,3,'which') ;
insert into packages values (57,3,'util-linux') ;
insert into packages values (58,3,'module-init-tools') ;
insert into packages values (59,3,'udev') ;
insert into packages values (60,3,'cracklib') ;
insert into packages values (122,3,'cracklib-dicts') ;
insert into packages values (123,3,'component-base-node') ;
  
# Setup the packages for the disked compute nodes
insert into packages values (61,4,'SysVinit') ;
insert into packages values (62,4,'basesystem') ;
insert into packages values (63,4,'bash') ;
insert into packages values (64,4,'redhat-release') ;
insert into packages values (65,4,'chkconfig') ;
insert into packages values (66,4,'coreutils') ;
insert into packages values (67,4,'db4') ;
insert into packages values (68,4,'e2fsprogs') ;
insert into packages values (69,4,'filesystem') ;
insert into packages values (70,4,'findutils') ;
insert into packages values (71,4,'gawk') ;
#insert into packages values (72,4,'glib') ;
insert into packages values (73,4,'glibc') ;
insert into packages values (74,4,'glibc-common') ;
insert into packages values (75,4,'initscripts') ;
insert into packages values (76,4,'iproute') ;
insert into packages values (77,4,'iputils') ;
insert into packages values (78,4,'krb5-libs') ;
insert into packages values (79,4,'libacl') ;
insert into packages values (80,4,'libattr') ;
insert into packages values (81,4,'libgcc') ;
insert into packages values (82,4,'libstdc++') ;
insert into packages values (83,4,'libtermcap') ;
insert into packages values (84,4,'mingetty') ;
insert into packages values (85,4,'mktemp') ;
insert into packages values (86,4,'ncurses') ;
insert into packages values (87,4,'net-tools') ;
insert into packages values (88,4,'nfs-utils') ;
insert into packages values (89,4,'pam') ;
insert into packages values (90,4,'pcre') ;
insert into packages values (91,4,'popt') ;
insert into packages values (92,4,'portmap') ;
insert into packages values (93,4,'procps') ;
insert into packages values (94,4,'psmisc') ;
insert into packages values (95,4,'rdate') ;
insert into packages values (96,4,'rsh') ;
insert into packages values (97,4,'rsh-server') ;
insert into packages values (98,4,'rsync') ;
insert into packages values (99,4,'sed') ;
insert into packages values (100,4,'setup') ;
insert into packages values (101,4,'shadow-utils') ;
insert into packages values (102,4,'openssh') ;
insert into packages values (103,4,'openssh-server') ;
insert into packages values (104,4,'sysklogd') ;
insert into packages values (105,4,'tcp_wrappers') ;
insert into packages values (106,4,'termcap') ;
insert into packages values (107,4,'tzdata') ;
insert into packages values (108,4,'util-linux') ;
insert into packages values (109,4,'words') ;
insert into packages values (110,4,'xinetd') ;
insert into packages values (111,4,'zlib') ;
insert into packages values (112,4,'tar') ;
insert into packages values (113,4,'mkinitrd') ;
insert into packages values (114,4,'less') ;
insert into packages values (115,4,'gzip') ;
insert into packages values (116,4,'which') ;
insert into packages values (117,4,'util-linux') ;
insert into packages values (118,4,'module-init-tools') ;
insert into packages values (119,4,'udev') ;
insert into packages values (120,4,'cracklib') ;
insert into packages values (121,4,'cracklib-dicts') ;
# id 122, 123 is used above
insert into packages values (124,4,'component-base-node') ;

# This is for testing dependencies on packages
insert into packages values (125,5,'python') ;
# Packages for the installer
insert into packages values (126, 1, 'booger-pack') ;
insert into packages values (127, 1, 'nuggets-pack') ;

# Setup the modules for the diskless compute nodes
insert into modules values (1,3,'nfs',1) ;
insert into modules values (2,3,'ext3',2) ;
insert into modules values (3,3,'bonding',3) ;
insert into modules values (4,3,'tg3',4) ;
insert into modules values (5,3,'bnx2',5) ;
insert into modules values (6,3,'e1000',6) ;
insert into modules values (7,3,'jbd',7) ;
insert into modules values (8,3,'lockd',8) ;
insert into modules values (9,3,'fscache',9) ;
insert into modules values (10,3,'nfs_acl',10) ;
insert into modules values (12,3,'sunrpc',11) ;
insert into modules values (13,3,'mii',12) ;
insert into modules values (14,3,'pcnet32',13) ;

# Setup the modules for the disked compute nodes
insert into modules values (20,4,'nfs',1) ;
insert into modules values (21,4,'ext3',2) ;
insert into modules values (22,4,'bonding',3) ;
insert into modules values (23,4,'tg3',4) ;
insert into modules values (24,4,'bnx2',5) ;
insert into modules values (25,4,'e1000',6) ;
insert into modules values (26,4,'mptscsih',7) ;
insert into modules values (27,4,'mptsas',8) ;
insert into modules values (28,4,'mptfc',9) ;
insert into modules values (29,4,'mptspi',10) ;
insert into modules values (30,4,'mptscsi',11) ;
insert into modules values (31,4,'mptbase',12) ;
insert into modules values (32,4,'jbd',13) ;
insert into modules values (33,4,'lockd',14) ;
insert into modules values (34,4,'fscache',15) ;
insert into modules values (35,4,'nfs_acl',16) ;
insert into modules values (36,4,'sunrpc',17) ;
insert into modules values (37,4,'mii', 18) ;
insert into modules values (38,4,'pcnet32', 19) ;

# Test for Fedora 7 installer (Replace e1000)
insert into modules values (39, 6, 'e1000', 1) ;

insert into appglobals values (1, 'ClusterName', 'BadBoy', NULL) ;
insert into appglobals values (2, 'DNSZone', 'myzone.company.com', NULL) ;
insert into appglobals values (3, 'DNSForwarders', '172.16.1.5,172.16.1.8', NULL) ;
insert into appglobals values (4, 'DNSSearch', 'myzone.company.com company.com corp.company.com', NULL) ;
insert into appglobals values (5, 'NASServer', '172.25.243.2', NULL) ;
insert into appglobals values (6, 'TimeZone', 'EST/EDT', NULL) ;
insert into appglobals values (7, 'NISDomain', 'engineering', 2) ;
insert into appglobals values (8, 'NISServers', '172.25.243.4,172.25.243.14', 2) ;
insert into appglobals values (9, 'NISDomain', 'testing', 3) ;
insert into appglobals values (10, 'NISServers', '172.25.243.99,172.25.243.100', 3) ;
insert into appglobals values (11, 'CFMSecret', 'GF5SEVTHJ589TNT45NTEYST78GYBG5GVYGT84NTV578TEB46', NULL) ;
insert into appglobals values (12, 'InstallerServeDNS', 'True', NULL) ;
insert into appglobals values (13, 'InstallerServeNIS', 'True', NULL) ;
insert into appglobals values (14, 'InstallerServeNFS', 'True', NULL) ;
insert into appglobals values (15, 'InstallerServeNTP', 'True', NULL) ;
insert into appglobals values (16, 'PrimaryInstaller', 'installer00', NULL) ;
insert into appglobals values (17, 'DHCPLeaseTime', '2400', NULL) ;
insert into appglobals values (18, 'InstallerServeSMTP', 'False', NULL) ;
insert into appglobals values (19, 'SMTPServer', 'mailserver.myzone.company.com', NULL) ;
insert into appglobals values (20, 'CFMBaseDir', '/opt/kusu/cfm', NULL) ;
insert into appglobals values (21, 'DEPOT_KITS_ROOT', '/depot/kits', 1) ;
insert into appglobals values (22, 'DEPOT_IMAGES_ROOT', '/depot/images', 1) ;
insert into appglobals values (23, 'DEPOT_REPOS_ROOT', '/depot/repos', 1) ;
insert into appglobals values (24, 'DEPOT_REPOS_SCRIPTS', '/depot/repos/custom_scripts', 1) ;
insert into appglobals values (25, 'DEPOT_REPOS_POST', '/depot/repos/post_scripts', 1) ;
insert into appglobals values (26, 'DEPOT_CONTRIB_ROOT', '/depot/contrib', 1) ;
insert into appglobals values (27, 'DEPOT_UPDATES_ROOT', '/depot/updates', 1) ;
insert into appglobals values (28, 'DEPOT_AUTOINST_ROOT', '/depot/repos/instconf', 1) ;
insert into appglobals values (29, 'PIXIE_ROOT', '/tftpboot/kusu', 1) ;
insert into appglobals values (30, 'PROVISION', 'KUSU', 1) ;

# Custom Scripts
insert into scripts values (1, 3, '/depot/repos/custom_scripts/bogus.sh') ;
insert into scripts values (2, 4, '/depot/repos/custom_scripts/bogus.sh') ;
insert into scripts values (3, 1, '/depot/repos/custom_scripts/bogus-installer.sh') ;
insert into scripts values (4, 1, '/depot/repos/custom_scripts/more-bogus-installer.sh') ;

# Components
insert into components values (1, 3, 'base-installer', 'This component provides the bits needed for installer nodes', 'fedora-6-i386') ;
insert into components values (2, 3, 'base-installer', 'This component provides the bits needed for installer nodes', 'rhel-5.1-i386') ;
insert into components values (3, 7, 'base-installer', 'This component provides the bits needed for installer nodes', 'fedora-7-x86_64') ;
insert into components values (4, 3, 'base-node', 'This component provides the bits needed for all nodes', 'fedora-6-i386') ;
insert into components values (5, 3, 'base-node', 'This component provides the bits needed for all nodes', 'rhel-5.1-i386') ;
insert into components values (6, 7, 'base-node', 'This component provides the bits needed for all nodes', 'fedora-7-x86_64') ;
insert into components values (7, 4, 'lsf-base', 'LSF BASE component for both FE & compute - runs on any fedora', 'fedora') ;
insert into components values (8, 4, 'lsf-server', 'LSF Server component - requires version 6 of fedora', 'fedora-6') ;
insert into components values (9, 4, 'lsf-compute', 'LSF compute component - doesnt care about the distro', NULL) ;
insert into components values (10, 1, 'fedora-6-i386', 'Component for FC6 x86 OS kit', 'fedora-6-i386') ;
insert into components values (11, 8, 'fedora-7-x86_64', 'Component for FC7 x86_64 OS kit', 'fedora-7-x86_64') ;
insert into components values (12, 9, 'vendor-drivers', 'Component for FC7 Drivers for D Vendor', 'fedora-7-x86_64') ;

# Driver packages
insert into driverpacks values (1, 11, 'kernel-2.6.21-1.3116.fc7.x86_64.rpm', 'Fedora 7 Kernel Package') ;
insert into driverpacks values (2, 12, 'e1000-7.3.15.3-sb_dkms.noarch.rpm', 'D Vendor e1000 Driver update') ;


# Nodegroup has Component
insert into ng_has_comp values (1, 1) ;
insert into ng_has_comp values (1, 4) ;
insert into ng_has_comp values (2, 4) ;
insert into ng_has_comp values (3, 4) ;
insert into ng_has_comp values (4, 4) ;
insert into ng_has_comp values (6, 3) ;
insert into ng_has_comp values (6, 6) ;
insert into ng_has_comp values (6, 11) ;
insert into ng_has_comp values (6, 12) ;
insert into ng_has_comp values (7, 6) ;
