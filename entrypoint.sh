#!/bin/bash

# The engine doesn't support connecting to Docker via unix socket.
# Bind it to a port instead.
if [ -a /var/run/docker.sock ]; then
    socat TCP-LISTEN:2375,fork UNIX-CONNECT:/var/run/docker.sock & disown
fi

exec storyscript-server start