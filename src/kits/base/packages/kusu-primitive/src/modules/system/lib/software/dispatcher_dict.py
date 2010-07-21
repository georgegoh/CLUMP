#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright 2010 Platform Computing Inc.
#
# The dispatcher dict is a python dictionary which catalogs several programs
# that are used for the same purpose in various distros. This layer of abstraction
# is not limited to commands and can be used for any purpose such as common directories
# or files which Kusu may depend on.

rhel_fedora_diskless_packages = ['OpenIPMI', 'OpenIPMI-libs', 'OpenIPMI-tools',
'SysVinit', 'autofs', 'basesystem', 'bash', 'chkconfig', 'coreutils', 'cracklib',
'cracklib-dicts', 'db4', 'dmidecode', 'e2fsprogs', 'filesystem', 'findutils',
'gawk', 'glibc', 'glibc-common', 'gzip', 'initscripts', 'iproute', 'iputils',
'krb5-libs', 'less', 'libacl', 'libattr', 'libgcc', 'libstdc++', 'libtermcap',
'mingetty', 'mkinitrd', 'mktemp', 'module-init-tools', 'ncurses', 'net-tools',
'nfs-utils', 'ntp', 'openssh', 'openssh-clients', 'openssh-server', 'pam',
'pcre', 'popt', 'portmap', 'procps', 'psmisc', 'rdate', 'rootfiles', 'rsh',
'rsh-server', 'rsync', 'rsyslog', 'sed', 'sendmail', 'setup', 'shadow-utils',
'sysklogd', 'tar', 'tcp_wrappers', 'termcap', 'tzdata', 'udev', 'util-linux',
'vim-common', 'vim-enhanced', 'vim-minimal', 'which', 'words', 'xinetd', 'yum',
'zlib', 'wget']

rhel_diskless_packages = rhel_fedora_diskless_packages + ['redhat-release',  'authconfig', 'redhat-lsb']
centos_diskless_packages = rhel_fedora_diskless_packages + ['authconfig', 'redhat-lsb']
sl_diskless_packages = rhel_fedora_diskless_packages + ['sl-release', 'authconfig', 'redhat-lsb']
slc_diskless_packages = rhel_fedora_diskless_packages + ['sl-release', 'authconfig', 'redhat-lsb']
fedora_diskless_packages =  rhel_fedora_diskless_packages + ['fedora-release']

rhel_imaged_packages = rhel_diskless_packages + ['grub', 'kernel']
fedora_imaged_packages = fedora_diskless_packages + ['grub', 'kernel']
sl_imaged_packages = sl_diskless_packages + ['grub', 'kernel']
slc_imaged_packages = slc_diskless_packages + ['grub', 'kernel']
centos_imaged_packages = centos_diskless_packages + ['grub', 'kernel']


standard_diskless_modules = ['uhci-hcd', 'ohci-hcd', 'ehci-hcd', 'jbd', 'nfs',
'ext3', 'libphy', 'tg3', 'bnx2', 'bnx2x', '8021q', 'igb', 'ixgbe', 'cxgb3',
'e1000', 'e1000e', 'mii', 'e100', 'lockd', 'nfs_acl', 'sunrpc', 'pcnet32',
'forcedeth', 'autofs4', 'ipmi_si', 'ipmi_devintf', 'ipmi_watchdog',
'ipmi_poweroff', 'ipmi_msghandler']

rhel_diskless_modules = standard_diskless_modules + ['fscache', 'dca']

standard_imaged_modules = ['uhci-hcd', 'ohci-hcd', 'ehci-hcd', 'jbd', 'nfs',
'ext3', 'libphy', 'tg3', 'bnx2', 'bnx2x', '8021q', 'igb', 'ixgbe', 'cxgb3',
'e1000', 'e1000e', 'scsi_mod', 'sd_mod', 'libata', 'ata_piix', 'sata_svw',
'sata_nv', 'ahci', 'mptbase', 'mptscsih', 'scsi_transport_sas',
'scsi_transport_fc', 'scsi_transport_spi', 'mptsas', 'mptfc', 'mptspi',
'mpt2sas', 'megaraid_sas', 'lockd', 'nfs_acl', 'sunrpc', 'mii', 'e100',
'pcnet32', 'forcedeth', 'autofs4', 'ipmi_si', 'ipmi_devintf', 'ipmi_watchdog',
'ipmi_poweroff', 'ipmi_msghandler', 'dm-mod']

rhel_imaged_modules = standard_imaged_modules + ['crypto_api', 'xfrm_nalgo',
'ipv6', 'bonding', 'fscache', 'dca']

sles_diskless_packages = ['OpenIPMI', 'aaa_base', 'aaa_skel', 'autofs', 'bash',
'binutils', 'coreutils', 'cracklib', 'cron', 'db', 'dhcpcd', 'e2fsprogs',
'ethtool', 'filesystem', 'findutils', 'gawk', 'glibc', 'glibc-i18ndata',
'glibc-locale', 'gzip', 'ipmitool', 'iproute2', 'iputils', 'klogd', 'krb5',
'less', 'libacl', 'libattr', 'libgcc', 'libstdc++', 'make', 'man', 'man-pages',
'mingetty', 'mkinitrd', 'mktemp', 'module-init-tools', 'ncurses', 'net-tools',
'nfs-utils', 'openssh', 'pam', 'patch', 'pcre', 'pmtools', 'popt', 'portmap',
'postfix', 'procps', 'psmisc', 'resmgr', 'rsh', 'rsh-server', 'rsync', 'sed',
'sles-release', 'syslog-ng', 'tar', 'tcpd', 'termcap', 'timezone', 'udev',
'util-linux', 'vim', 'wireless-tools', 'words', 'xinetd', 'xntp', 'zlib',
'zypper']

sles_imaged_packages = sles_diskless_packages + ['grub', 'kernel-default', 'hwinfo', 'mdadm']

sles_diskless_modules = standard_diskless_modules + ['usbcore', 'af_packet', 'firmware_class']
sles_imaged_modules = standard_imaged_modules + ['usbcore', 'af_packet', 'firmware_class']

dispatcher_dict = {
    'service_start' : { ('SLES','10','i386') : 'service %s start',
                        ('SLES','10','x86_64') : 'service %s start',
                        ('RHEL','5','i386') : 'service %s start',
                        ('RHEL','5','x86_64') : 'service %s start',
                      },
    'service_stop' : { ('SLES','10','i386') : 'service %s stop',
                       ('SLES','10','x86_64') : 'service %s stop',
                       ('RHEL','5','i386') : 'service %s stop',
                       ('RHEL','5','x86_64') : 'service %s stop',
                     },
    'service_restart' : { ('SLES','10','i386') : 'service %s restart',
                          ('SLES','10','x86_64') : 'service %s restart',
                          ('RHEL','5','i386') : 'service %s restart',
                          ('RHEL','5','x86_64') : 'service %s restart',
                        },
    'service_status' : { ('SLES','10','i386') : 'service %s status' ,
                         ('SLES','10','x86_64') : 'service %s status',
                         ('RHEL','5','i386') : 'service %s status',
                         ('RHEL','5','x86_64') : 'service %s status',
                       },
    'service_enable' : { ('SLES','10','i386') : 'chkconfig %s on',
                         ('SLES','10','x86_64') : 'chkconfig %s on',
                         ('RHEL','5','i386') : 'chkconfig %s on',
                         ('RHEL','5','x86_64') : 'chkconfig %s on',
                       },
    'service_disable' : { ('SLES','10','i386') : 'chkconfig %s off',
                          ('SLES','10','x86_64') : 'chkconfig %s off',
                          ('RHEL','5','i386') : 'chkconfig %s off',
                          ('RHEL','5','x86_64') : 'chkconfig %s off',
                        },
    'service_list_all' : { ('SLES','10','i386') : 'chkconfig --list',
                           ('SLES','10','x86_64') : 'chkconfig --list',
                           ('RHEL','5','i386') : 'chkconfig --list',
                           ('RHEL','5','x86_64') : 'chkconfig --list',
                         },
    # TODO: A way to make this completely generic so that the calling tool eg: svctool does not
    # have to grep for various phrases to make sense of the output will be good.
    'service_runningp' : { ('SLES','10','i386') : 'service %s status',
                           ('SLES','10','x86_64') : 'service %s status',
                           ('RHEL','5','i386') : 'service %s status',
                           ('RHEL','5','x86_64') : 'service %s status',
                         },
    'service_enabledp' : { ('SLES','10','i386') : 'service %s status',
                           ('SLES','10','x86_64') : 'service %s status',
                           ('RHEL','5','i386') : 'service %s status',
                           ('RHEL','5','x86_64') : 'service %s status',
                         },
    'service_disabledp' : { ('SLES','10','i386') : 'service %s status',
                            ('SLES','10','x86_64') : 'service %s status',
                            ('RHEL','5','i386') : 'service %s status',
                            ('RHEL','5','x86_64') : 'service %s status',
                          },
    'service_exists' : { ('SLES','10','i386') : '/etc/init.d/%s',
                         ('SLES','10','x86_64') : '/etc/init.d/%s',
                         ('RHEL','5','i386') : '/etc/init.d/%s',
                         ('RHEL','5','x86_64') : '/etc/init.d/%s',
                          },
    'webserver' : { ('SLES','10','i386') : 'apache2',
                    ('SLES','10','x86_64') : 'apache2',
                    ('RHEL','5','i386') : 'httpd',
                    ('RHEL','5','x86_64') : 'httpd',
                  },
    'webserver_usergroup': { ('SLES','10','i386') : ('wwwrun', 'www'),
                             ('SLES','10','x86_64') : ('wwwrun', 'www'),
                             ('RHEL','5','i386') : ('apache', 'apache'),
                             ('RHEL','5','x86_64') : ('apache', 'apache'),
                           },
    'default_webserver_usergroup_ids': { ('SLES','10','i386') : ('30', '8'),
                                         ('SLES','10','x86_64') : ('30', '8'),
                                         ('RHEL','5','i386') : ('48', '48'),
                                         ('RHEL','5','x86_64') : ('48', '48'),
                                       },
    'webserver_docroot': { ('SLES','10','i386') : '/srv/www/htdocs',
                           ('SLES','10','x86_64') : '/srv/www/htdocs',
                           ('RHEL','5','i386') : '/var/www/html',
                           ('RHEL','5','x86_64') : '/var/www/html',
                         },
    'webserver_confdir': { ('SLES','10','i386') : '/etc/apache2/conf.d',
                           ('SLES','10','x86_64') : '/etc/apache2/conf.d',
                           ('RHEL','5','i386') : '/etc/httpd/conf.d',
                           ('RHEL','5','x86_64') : '/etc/httpd/conf.d',
                         },
    'pxelinux0_path': { ('SLES','10','i386') : '/usr/share/syslinux/pxelinux.0',
                        ('SLES','10','x86_64') : '/usr/share/syslinux/pxelinux.0',
                        ('RHEL','5','i386') : '/usr/lib/syslinux/pxelinux.0',
                        ('RHEL','5','x86_64') : '/usr/lib/syslinux/pxelinux.0',
                      },
    'networkscripts_path': { ('SLES','10','i386') : '/etc/sysconfig/network',
                             ('SLES','10','x86_64') : '/etc/sysconfig/network',
                             ('RHEL','5','i386') : '/etc/sysconfig/network-scripts',
                             ('RHEL','5','x86_64') : '/etc/sysconfig/network-scripts',
                           },
    'ifup_path': { ('SLES','10','i386') : '/sbin',
                   ('SLES','10','x86_64') : '/sbin',
                   ('RHEL','5','i386') : '/sbin',
                   ('RHEL','5','x86_64') : '/sbin',
                 },
    'tftp_conf' : { ('SLES','10','i386') : '/etc/xinetd.d/tftp',
                    ('SLES','10','x86_64') : '/etc/xinetd.d/tftp',
                    ('RHEL','5','i386') : '/etc/xinetd.d/tftp',
                    ('RHEL','5','x86_64') : '/etc/xinetd.d/tftp',
                  },
    'ntp_server' : { ('SLES','10','i386') : 'ntp',
                     ('SLES','10','x86_64') : 'ntp',
                     ('RHEL','5','i386') : 'ntpd',
                     ('RHEL','5','x86_64') : 'ntpd',
                   },
    'named_dir' : { ('SLES','10','i386') : '/var/lib/named',
                    ('SLES','10','x86_64') : '/var/lib/named',
                    ('RHEL','5','i386') : '/var/named',
                    ('RHEL','5','x86_64') : '/var/named',
                  },
    'nfsserver' : { ('SLES','10','i386') : 'nfsserver',
                    ('SLES','10','x86_64') : 'nfsserver',
                    ('RHEL','5','i386') : 'nfs',
                    ('RHEL','5','x86_64') : 'nfs',
                  },
    'mysql_server' : { ('SLES','10','i386') : 'mysql',
                       ('SLES','10','x86_64') : 'mysql',
                       ('RHEL','5','i386') : 'mysqld',
                       ('RHEL','5','x86_64') : 'mysqld',
                     },

    'postgres_server' : { ('SLES','10','i386') : 'postgresql',
                       ('SLES','10','x86_64') : 'postgresql',
                       ('RHEL','5','i386') : 'postgresql',
                       ('RHEL','5','x86_64') : 'postgresql',
                     },

    'ipmi_service' : { ('SLES','10','i386') : 'ipmi',
                       ('SLES','10','x86_64') : 'ipmi',
                       ('RHEL','5','i386') : 'ipmi',
                       ('RHEL','5','x86_64') : 'ipmi',
                     },

    'cups_service' : { ('SLES','10','i386') : 'cups',
                       ('SLES','10','x86_64') : 'cups',
                       ('RHEL','5','i386') : 'cups',
                       ('RHEL','5','x86_64') : 'cups',
                     },

    'gpm_service' : { ('SLES','10','i386') : 'gpm',
                       ('SLES','10','x86_64') : 'gpm',
                       ('RHEL','5','i386') : 'gpm',
                       ('RHEL','5','x86_64') : 'gpm',
                     },

    'pcsc_service' : { ('SLES','10','i386') : 'pcscd',
                       ('SLES','10','x86_64') : 'pcscd',
                       ('RHEL','5','i386') : 'pcscd',
                       ('RHEL','5','x86_64') : 'pcscd',
                     },

    'logging_service' : { ('SLES','10','i386') : 'syslog',
                         ('SLES','10','x86_64') : 'syslog',
                         ('RHEL','5','i386') : 'rsyslog',
                         ('RHEL','5','x86_64') : 'rsyslog',
                     },

    'multi-category_service' : {('RHEL','5','i386') : 'mcstrans',
                  ('RHEL','5','x86_64') : 'mcstrans',
                 },

    'avahi_service' : {('RHEL','5','i386') : 'avahi-daemon',
                  ('RHEL','5','x86_64') : 'avahi-daemon',
                 },

    'restorecond_service' : {('RHEL','5','i386') : 'restorecond',
                  ('RHEL','5','x86_64') : 'restorecond',
                 },

    'bluetooth_service' : {('RHEL','5','i386') : 'bluetooth',
                  ('RHEL','5','x86_64') : 'bluetooth',
                 },

    'bluetooth_hid_service' : {('RHEL','5','i386') : 'hidd',
                  ('RHEL','5','x86_64') : 'hidd',
                 },

    'os_update_service' : {('RHEL','5','i386') : 'rhnsd',
                  ('RHEL','5','x86_64') : 'rhnsd',
                 },

    'hardware_detect_service' : {('RHEL','5','i386') : 'kudzu',
                  ('RHEL','5','x86_64') : 'kudzu',
                 },

    'kparams' : { ('SLES','10','i386') : 'textmode=1',
                  ('SLES','10','x86_64') : 'textmode=1',
                  ('RHEL','5','i386') : 'text noipv6 kssendmac selinux=0',
                  ('RHEL','5','x86_64') : 'text noipv6 kssendmac selinux=0',
                },
    'autoinstall_conf' : { ('SLES','10','i386') : 'autoinst.xml',
                           ('SLES','10','x86_64') : 'autoinst.xml',
                           ('RHEL','5','i386') : 'ks.cfg',
                           ('RHEL','5','x86_64') : 'ks.cfg',
                         },
    'autoinstall_type' : { ('SLES','10','i386') : 'autoyast',
                           ('SLES','10','x86_64') : 'autoyast',
                           ('RHEL','5','i386') : 'kickstart',
                           ('RHEL','5','x86_64') : 'kickstart',
                         },
    'yum_repo_subdir' : { ('RHEL','5','i386') : '/Server/',
                          ('RHEL','5','x86_64') : '/Server/',
                          ('CENTOS','5','i386') : '',
                          ('CENTOS','5','x86_64') : '',
                          ('SCIENTIFICLINUX','5','i386') : '/SL/',
                          ('SCIENTIFICLINUX','5','x86_64') : '/SL/',
                          ('SCIENTIFICLINUXCERN','5','i386') : '/SL/',
                          ('SCIENTIFICLINUXCERN','5','x86_64') : '/SL/',
                          ('FEDORA','6','i386') : '',
                          ('FEDORA','6','x86_64') : '',
                        },
    'zypper_base_dir' : { ('SLES','10','i386') : '/var/lib/zypp',
                          ('SLES','10','x86_64') : '/var/lib/zypp',
                        },
    'zypper_sources_dir' : { ('SLES','10','i386') : '/var/lib/zypp/db/sources',
                             ('SLES','10','x86_64') : '/var/lib/zypp/db/sources',
                             ('OPENSUSE','10.3','i386') : '/etc/zypp/repos.d',
                             ('OPENSUSE','10.3','x86_64') : '/etc/zypp/repos.d',
                           },
    'zypper_cache_dir' : { ('SLES','10','i386') : '/var/lib/zypp/cache',
                           ('SLES','10','x86_64') : '/var/lib/zypp/cache',
                           ('OPENSUSE','10.3','i386') : '/var/cache/zypp',
                           ('OPENSUSE','10.3','x86_64') : '/var/cache/zypp',
                         },
    'zypper_update_cmd' : { ('SLES','10','i386') : '/usr/bin/zypper --non-interactive --no-gpg-checks update -t package --auto-agree-with-licenses',
                            ('SLES','10','x86_64') : '/usr/bin/zypper --non-interactive --no-gpg-checks update -t package --auto-agree-with-licenses',
                            ('SLES','10.1','i386') : '/usr/bin/zypper --non-interactive update -t package',
                            ('SLES','10.1','x86_64') : '/usr/bin/zypper --non-interactive update -t package',
                          },
    'zypper_install_cmd' : { ('SLES','10','i386') : '/usr/bin/zypper --non-interactive --no-gpg-checks install --auto-agree-with-licenses',
                            ('SLES','10','x86_64') : '/usr/bin/zypper --non-interactive --no-gpg-checks install --auto-agree-with-licenses',
                            ('SLES','10.1','i386') : '/usr/bin/zypper --non-interactive install',
                            ('SLES','10.1','x86_64') : '/usr/bin/zypper --non-interactive install',
                          },
    'zypper_remove_cmd' : { ('SLES','10','i386') : '/usr/bin/zypper --non-interactive --no-gpg-checks remove',
                            ('SLES','10','x86_64') : '/usr/bin/zypper --non-interactive --no-gpg-checks remove',
                            ('SLES','10.1','i386') : '/usr/bin/zypper --non-interactive remove',
                            ('SLES','10.1','x86_64') : '/usr/bin/zypper --non-interactive remove',
                          },

    'syslog_reconfig_cmd' : { ('SLES','10','i386') : '/sbin/SuSEconfig --module syslog-ng',
                              ('SLES','10','x86_64') : '/sbin/SuSEconfig --module syslog-ng',
                            },

    'firewall_start' : { ('SLES','10','i386') : 'SuSEfirewall2 start',
                         ('SLES','10','x86_64') : 'SuSEfirewall2 start',
                         ('RHEL','5','i386') : 'service iptables start',
                         ('RHEL','5','x86_64') : 'service iptables start',
                       },
    'firewall_stop' : { ('SLES','10','i386') : 'SuSEfirewall2 stop',
                        ('SLES','10','x86_64') : 'SuSEfirewall2 stop',
                        ('RHEL','5','i386') : 'service iptables stop',
                        ('RHEL','5','x86_64') : 'service iptables stop',
                      },
    'firewall_status' : { ('SLES','10','i386') : 'SuSEfirewall2 status',
                          ('SLES','10','x86_64') : 'SuSEfirewall2 status',
                          ('RHEL','5','i386') : 'service iptables status',
                          ('RHEL','5','x86_64') : 'service iptables status',
                        },
    'firewall_restart' : { ('SLES','10','i386') : 'SuSEfirewall2 stop; SuSEfirewall2 start',
                           ('SLES','10','x86_64') : 'SuSEfirewall2 stop; SuSEfirewall2 start',
                           ('RHEL','5','i386') : 'service iptables restart',
                           ('RHEL','5','x86_64') : 'service iptables restart',
                         },
    'firewall_enable' : { ('SLES','10','i386') : 'SuSEfirewall2 on',
                          ('SLES','10','x86_64') : 'SuSEfirewall2 on',
                          ('RHEL','5','i386') : 'chkconfig iptables on',
                          ('RHEL','5','x86_64') : 'chkconfig iptables on',
                        },
    'firewall_disable' : { ('SLES','10','i386') : 'SuSEfirewall2 off',
                           ('SLES','10','x86_64') : 'SuSEfirewall2 off',
                           ('RHEL','5','i386') : 'chkconfig iptables off',
                           ('RHEL','5','x86_64') : 'chkconfig iptables off',
                         },
    'pmc_restart' : { ('SLES','10','i386') : 'service pmc stop; service pmc start',
                      ('SLES','10','x86_64') : 'service pmc stop; service pmc start',
                      ('RHEL','5','i386') : 'service pmc stop; service pmc start',
                      ('RHEL','5','x86_64') : 'service pmc stop; service pmc start',
                         },
    'makedev' : { ('SLES','10','i386') : 'MAKEDEV',
                  ('SLES','10','x86_64') : 'MAKEDEV',
                  ('RHEL','5','i386') : 'MAKEDEV -d $FAKEROOT/dev -x',
                  ('RHEL','5','x86_64') : 'MAKEDEV -d $FAKEROOT/dev -x',
                },
    'inst_conf_plugin' : { ('SLES','10','i386') : 'autoinst',
                           ('SLES','10','x86_64') : 'autoinst',
                           ('RHEL','5','i386') : 'kickstart',
                           ('RHEL','5','x86_64') : 'kickstart',
                         },
    'diskless_packages' : { ('SLES','10','i386') : sles_diskless_packages,
                            ('SLES','10','x86_64') : sles_diskless_packages,
                            ('CENTOS','5','i386') : centos_diskless_packages,
                            ('CENTOS','5','x86_64') : centos_diskless_packages,
                            ('RHEL','5','i386') : rhel_diskless_packages,
                            ('RHEL','5','x86_64') : rhel_diskless_packages,
                            ('FEDORA','6','i386') : fedora_diskless_packages,
                            ('FEDORA','6','x86_64') : fedora_diskless_packages,
                            ('SCIENTIFICLINUX','5','i386') : sl_diskless_packages,
                            ('SCIENTIFICLINUX','5','x86_64') : sl_diskless_packages,
                            ('SCIENTIFICLINUXCERN','5','i386') : slc_diskless_packages,
                            ('SCIENTIFICLINUXCERN','5','x86_64') : slc_diskless_packages,
                          },
    'imaged_packages' : { ('SLES','10','i386') : sles_imaged_packages,
                          ('SLES','10','x86_64') : sles_imaged_packages,
                          ('CENTOS','5','i386') : centos_imaged_packages,
                          ('CENTOS','5','x86_64') : centos_imaged_packages,
                          ('RHEL','5','i386') : rhel_imaged_packages,
                          ('RHEL','5','x86_64') : rhel_imaged_packages,
                          ('FEDORA','6','i386') : fedora_imaged_packages,
                          ('FEDORA','6','x86_64') : fedora_imaged_packages,
                          ('SCIENTIFICLINUX','5','i386') : sl_imaged_packages,
                          ('SCIENTIFICLINUX','5','x86_64') : sl_imaged_packages,
                          ('SCIENTIFICLINUXCERN','5','i386') : slc_imaged_packages,
                          ('SCIENTIFICLINUXCERN','5','x86_64') : slc_imaged_packages,
                        },
    'diskless_modules' : { ('SLES','10','i386') : sles_diskless_modules,
                           ('SLES','10','x86_64') : sles_diskless_modules,
                           ('RHEL','5','i386') : rhel_diskless_modules,
                           ('RHEL','5','x86_64') : rhel_diskless_modules,
                         },
    'imaged_modules' : { ('SLES','10','i386') : sles_imaged_modules,
                         ('SLES','10','x86_64') : sles_imaged_modules,
                         ('RHEL','5','i386') : rhel_imaged_modules,
                         ('RHEL','5','x86_64') : rhel_imaged_modules,
                       },
    'default_fstype' : { ('SLES','10','i386'): 'ext3',
                         ('SLES','10','x86_64'): 'ext3',
                         ('OPENSUSE','10.3', 'i386'): 'ext3',
                         ('OPENSUSE', '10.3', 'x86_64'): 'ext3',
                         ('RHEL','5','i386'): 'ext3',
                         ('RHEL','5','x86_64'): 'ext3',
                       },
    'ntop_conf' : { ('SLES','10','i386'): '/etc/sysconfig/ntop',
                    ('SLES','10','x86_64'): '/etc/sysconfig/ntop',
                    ('RHEL','5','i386'): '/etc/ntop.conf',
                    ('RHEL','5','x86_64'): '/etc/ntop.conf',
                  },
    'syslog_conf' : { ('SLES','10','i386'): '/etc/syslog-ng/syslog-ng.conf.in',
                      ('SLES','10','x86_64'): '/etc/syslog-ng/syslog-ng.conf.in',
                      ('OPENSUSE','10.3', 'i386'): '/etc/syslog-ng/syslog-ng.conf',
                      ('OPENSUSE', '10.3', 'x86_64'): '/etc/syslog-ng/syslog-ng.conf',
                      ('RHEL','5','i386'): '/etc/rsyslog.conf',
                      ('RHEL','5','x86_64'): '/etc/rsyslog.conf',
                    },

    'syslog_conf_tmpl' : { ('SLES','10','i386'): '/opt/kusu/etc/templates/syslog-ng.conf.in.tmpl',
                           ('SLES','10','x86_64'): '/opt/kusu/etc/templates/syslog-ng.conf.in.tmpl',
                           ('RHEL','5','i386'): '/opt/kusu/etc/templates/rsyslog_conf.tmpl',
                           ('RHEL','5','x86_64'): '/opt/kusu/etc/templates/rsyslog_conf.tmpl',
                         },

    'firefox_user_prefs' : { ('SLES','10','i386'): '/usr/lib/firefox',
                             ('SLES','10','x86_64'): '/usr/lib/firefox',
                             ('RHEL','5','i386'): '/usr/lib/firefox',
                             ('RHEL','5','x86_64'): '/usr/lib64/firefox',
                           },
    'network_config_files' : { ('SLES','10','i386') : '/etc/sysconfig/network/ifcfg-eth-id-*',
                               ('SLES','10','x86_64') : '/etc/sysconfig/network/ifcfg-eth-id-*',
                               ('RHEL','5','i386') : '/etc/sysconfig/network-scripts/ifcfg-*',
                               ('RHEL','5','x86_64') : '/etc/sysconfig/network-scripts/ifcfg-*'
                             },
    'dhcpd_interface_arg' : { ('SLES','10','i386') : 'DHCPD_INTERFACE',
                              ('SLES','10','x86_64') : 'DHCPD_INTERFACE',
                              ('RHEL','5','i386') : 'DHCPDARGS',
                              ('RHEL','5','x86_64') : 'DHCPDARGS'
                            },
    'dhcp_server_package' : { ('SLES','10','i386') : 'dhcp-server',
                              ('SLES','10','x86_64') : 'dhcp-server',
                              ('RHEL','5','i386') : 'dhcp',
                              ('RHEL','5','x86_64') : 'dhcp'
                            },
    'firewall_config_file' : { ('SLES','10','i386') : '/etc/sysconfig/SuSEfirewall2',
                               ('SLES','10','x86_64') : '/etc/sysconfig/SuSEfirewall2',
                               ('RHEL','5','i386') : '/etc/sysconfig/iptables',
                               ('RHEL','5','x86_64') : '/etc/sysconfig/iptables',
                             },
    'rpm_gpg_key' : { ('CENTOS','5','i386') : '/etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-5',
                      ('CENTOS','5','x86_64') : '/etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-5',
                      ('RHEL','5','i386') : '/etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release',
                      ('RHEL','5','x86_64') : '/etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release',
                      ('SCIENTIFICLINUX','5','i386') : '/etc/pki/rpm-gpg/RPM-GPG-KEY',
                      ('SCIENTIFICLINUX','5','x86_64') : '/etc/pki/rpm-gpg/RPM-GPG-KEY',
                      ('SCIENTIFICLINUXCERN','5','i386') : '/etc/pki/rpm-gpg/RPM-GPG-KEY',
                      ('SCIENTIFICLINUXCERN','5','x86_64') : '/etc/pki/rpm-gpg/RPM-GPG-KEY',
                    }
    }

if __name__ == '__main__':
    print  dispatcher_dict
    for os_command_map in dispatcher_dict.values():
        for os_tuple in os_command_map.keys():
             if 'SLES' in os_tuple:
                 if 1 == str(os_command_map[os_tuple]).count('%s') :
                     print os_command_map[os_tuple] % 'test'
                 else:
                     print os_command_map[os_tuple]

