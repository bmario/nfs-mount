#!/bin/bash	

cp nfs-mount-export /etc/init.d/nfs-mount-export
cp nfs-mount-exporter.py /usr/bin/nfs-mount-exporter.py

update-rc.d nfs-mount-export defaults 90
