#!/usr/bin/python
#
#       nfsmount-exporter.py Version 0.1
#
#       Copyright 2008 Mario Bielert <bmario@dragon-soft.de>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.


import dbus
import avahi
import os

serviceType = "_nfs._tcp" # See http://www.dns-sd.org/ServiceTypes.html
servicePort = 2049        # default NFS port
serviceTXT = "path="      # TXT record for the service

if __name__ == '__main__':

    bus = dbus.SystemBus()

    server = dbus.Interface(
            bus.get_object( avahi.DBUS_NAME, avahi.DBUS_PATH_SERVER ),
            avahi.DBUS_INTERFACE_SERVER )

    hostname = server.GetHostNameFqdn()

    fobj = open("/etc/exports", "r")

    for line in fobj:
        if line[0] != "#":
            line = line[:line.find(" ")]
            path = line

            os.system('avahi-publish-service "%s:%s" %s %s "%s%s" &' % (hostname, path, serviceType, servicePort, serviceTXT, path))

    fobj.close()

