#!/bin/bash

rm /etc/init.d/nfs-mount-export
rm /usr/bin/nfs-mount-exporter.py

if [ -e /usr/bin/nfs-mount-unexporter.py ]
then
    rm /usr/bin/nfs-mount-unexporter.py
fi

update-rc.d nfs-mount-export remove
