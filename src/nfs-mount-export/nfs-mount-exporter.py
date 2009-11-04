#!/usr/bin/python
#
#       nfsmount-exporter.py Version 0.2
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
import gobject
import os
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

serviceType = "_nfs._tcp" # See http://www.dns-sd.org/ServiceTypes.html
servicePort = 2049        # default NFS port
serviceTXT = "path="      # TXT record for the service
serviceDomain = "local"

if __name__ == '__main__':

    bus = dbus.SystemBus()

    server = dbus.Interface(
            bus.get_object( avahi.DBUS_NAME, avahi.DBUS_PATH_SERVER ),
            avahi.DBUS_INTERFACE_SERVER )

    hostname = server.GetHostNameFqdn()

    group = dbus.Interface(bus.get_object(avahi.DBUS_NAME, server.EntryGroupNew()), avahi.DBUS_INTERFACE_ENTRY_GROUP)

    fobj = open("/etc/exports", "r")

    for line in fobj:
        line = line.strip()
        line = line.replace("\t", "    ")
        if line[0] != "#":
            line = line[:line.find(" ")]
            path = line
            
            name = "%s:%s" % (hostname, path)
            txt = "%s%s" % (serviceTXT, path)
            
            group.AddService(avahi.IF_UNSPEC, avahi.PROTO_INET, dbus.UInt32(0), name, serviceType, serviceDomain, hostname, dbus.UInt16(servicePort), avahi.string_array_to_txt_array([txt]))
            


#            os.system('avahi-publish-service "%s:%s" %s %s "%s%s" &' % (hostname, path, serviceType, servicePort, serviceTXT, path))

    fobj.close()
    
    group.Commit()
    
main_loop = gobject.MainLoop()
main_loop.run()

