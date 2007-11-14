#!/bin/sh

/bin/cat << 'EOF' > /opt/kusu/lib/plugins/cfmclient/component-cacti.remove
#!/bin/sh

rpm -e cacti cacti-cactid > /dev/null 2>&1
rpm -e net-snmp net-snmp-libs net-snmp-utils php-snmp rrdtool > /dev/null 2>&1

rm -f /opt/kusu/lib/plugins/cfmclient/component-cacti.remove
EOF
