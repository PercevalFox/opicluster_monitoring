#!/bin/sh
test -f /data/ip_threat.prom && \
find /data/ip_threat.prom -mmin -65 | grep -q ip_threat.prom