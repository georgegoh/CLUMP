#!/bin/sh

/bin/cat << 'EOF' > /opt/kusu/lib/plugins/cfmclient/nagios-installer.remove
#!/bin/sh

rpm -e nagios-plugins-procs nagios-plugins-ssh nagios-plugins-real nagios-plugins-hpjd nagios-plugins-wave nagios-plugins-breeze nagios-plugins-oracle nagios-plugins-dhcp nagios-plugins-dig nagios-plugins-smtp nagios-plugins-disk_smb nagios-plugins-snmp nagios-plugins-apt nagios-plugins-disk nagios-plugins-mrtgtraf nagios-plugins-mrtg nagios-plugins-overcr nagios-plugins-ups nagios-plugins-swap nagios-plugins-ide_smart nagios-plugins-nwstat nagios-plugins-dummy nagios-plugins-perl nagios-plugins-file_age nagios-plugins-linux_raid nagios-plugins-flexlm nagios-plugins-log nagios-plugins-udp nagios-plugins-pgsql nagios-plugins-mysql nagios-plugins-ldap nagios-plugins-http nagios-plugins-dns nagios-plugins-tcp nagios-plugins-by_ssh nagios-plugins-mailq nagios-plugins-ntp nagios-plugins-ping nagios-plugins-users nagios-plugins-time nagios-plugins-nagios nagios-plugins-nt nagios-plugins-load nagios-plugins-rpc nagios-plugins-ircd nagios-plugins-sensors nagios-plugins-icmp nagios-plugins-nrpe
rpm -e nagios-plugins
rpm -e kusu-nagios-extras nagios

rm -f /opt/kusu/lib/plugins/cfmclient/nagios-installer.remove
EOF
