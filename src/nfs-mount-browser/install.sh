#!/bin/bash
cp nfsmount.conf /etc/dbus-1/system.d/nfsmount.conf
cp nfs-mount-browser /etc/init.d/nfs-mount-browser
cp nfs-mount-browser.py /usr/local/sbin/nfs-mount-browser.py
update-rc.d nfs-mount-browser defaults 90

