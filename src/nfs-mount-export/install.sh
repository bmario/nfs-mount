#!/bin/bash	

cp nfs-mount-export /etc/init.d/nfs-mount-export
chmod +x /etc/init.d/nfs-mount-export
cp nfs-mount-exporter.py /usr/local/sbin/nfs-mount-exporter.py
chmod +x /usr/local/sbin/nfs-mount-exporter.py
update-rc.d nfs-mount-export defaults 90
