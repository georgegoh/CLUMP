#!/bin/sh

/bin/cat << 'EOF' > /opt/kusu/lib/plugins/cfmclient/nagios-installer.remove
#!/bin/sh

rpm -e nagios nagios-plugins nagios-plugin-mysql nagios-plugin-nrpe perl-Crypt-DES perl-Net-SNMP

rm -f /opt/kusu/lib/plugins/cfmclient/nagios-installer.remove
EOF
