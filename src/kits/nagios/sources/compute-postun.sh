#!/bin/sh

/bin/cat << 'EOF' > /opt/kusu/lib/plugins/cfmclient/nagios-compute.remove
#!/bin/sh

rpm -e nagios-nrpe nagios-plugins nagios-plugin-nrpe perl-Crypt-DES perl-Net-SNMP

rm -f /opt/kusu/lib/plugins/cfmclient/nagios-compute.remove
EOF
