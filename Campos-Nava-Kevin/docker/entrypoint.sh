#!/bin/bash
set -e
mkdir -p /root/.ssh
chmod 700 /root/.ssh
if [ -f /tmp/authorized_keys ]; then
    cp /tmp/authorized_keys /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
fi
exec "$@"
