#!/bin/sh
# Copy SSH keys from mounted read-only volume and fix permissions
if [ -d /root/.ssh-mount ]; then
    cp -r /root/.ssh-mount/* /root/.ssh/ 2>/dev/null
    chmod 700 /root/.ssh
    chmod 600 /root/.ssh/* 2>/dev/null
    chmod 644 /root/.ssh/*.pub 2>/dev/null
fi

exec "$@"
