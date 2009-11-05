#!/bin/bash

rm /etc/init.d/nfs-mount-export
rm /usr/local/sbin/nfs-mount-exporter.py

update-rc.d nfs-mount-export remove
