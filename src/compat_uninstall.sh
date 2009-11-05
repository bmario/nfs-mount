#!/bin/bash

echo "This script uninstalls all nfs-mount script's located at the old path's"

echo "Uninstalling nfs-mount-browser..."
if [ -f /usr/bin/nfs-mount-browser.py ] then
rm /etc/dbus-1/system.d/nfsmount.conf
rm /etc/init.d/nfs-mount-browser
rm /usr/bin/nfs-mount-browser.py
update-rc.d nfs-mount-browser remove > /dev/null
fi
echo "Done."


echo "Uninstalling nfs-mount-exporter..."
if [ -f /usr/bin/nfs-mount-exporter.py ] then
rm /usr/bin/nfs-mount-exporter.py
rm /etc/init.d/nfs-mount-export
update-rc.d nfs-mount-export remove > /dev/null
fi 
echo "Done."

echo "Uninstalling nfs-mount-exporter..."
if [ -f /usr/bin/nfs-mount-systray.py ] then
rm /usr/bin/nfs-mount-systray.py
rm /etc/xdg/autostart/Nfs\ Browser.desktop
fi
echo "Done."

echo "Everything is done."
