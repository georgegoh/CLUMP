#!/bin/sh

/bin/cat << 'EOF' > /opt/kusu/lib/plugins/cfmclient/cacti-monitored-node.remove
#!/bin/sh

rpm -e cacti-node > /dev/null 2>&1

rm -f /opt/kusu/lib/plugins/cfmclient/cacti-monitored-node.remove
EOF
