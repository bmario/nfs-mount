#!/bin/bash
rm /etc/dbus-1/system.d/nfsmount.conf
rm /etc/init.d/nfs-mount-browser
rm /usr/bin/nfs-mount-browser.py

update-rc.d nfs-mount-browser remove
