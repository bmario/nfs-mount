#!/bin/bash
rm /etc/dbus-1/system.d/nfsmount.conf
rm /etc/init.d/nfs-mount-browser
rm /usr/local/sbin/nfs-mount-browser.py

update-rc.d nfs-mount-browser remove
