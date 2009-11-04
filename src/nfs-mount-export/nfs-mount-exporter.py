#!/usr/bin/python
# -*- coding: utf-8 -*-
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

from dbus import SystemBus, Interface, UInt32, UInt16
from avahi import DBUS_NAME, DBUS_PATH_SERVER, DBUS_INTERFACE_SERVER, IF_UNSPEC, PROTO_INET, strink_array_to_txt_array
from gobject import MainLoop
from os import access, F_OK, R_OK
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

serviceType = "_nfs._tcp" # See http://www.dns-sd.org/ServiceTypes.html
servicePort = 2049        # default NFS port
serviceTXTPrefix = "path="      # TXT record for the service
serviceDomain = "local"

def parse_shares(filename='/etc/default'):
    """
    Parses NFS Shares from filename.

    Returns: List of Shares
    """
    shares = []
    f = open(filename, 'r')
    for line in f.readlines():
        if line.strip()[0] == '#': continue
        normalized_line = line.strip().replace('\t','    ')
        path = normalized_line.split()[0]
        shares.append(path)
    f.close()
    return shares
# We are a Script, lets go!
if __name__ == '__main__':
    bus = SystemBus()
    server = Interface(
            bus.get_object( DBUS_NAME, DBUS_PATH_SERVER ),
            DBUS_INTERFACE_SERVER )
    hostname = server.GetHostNameFqdn()
    group = Interface(bus.get_object(DBUS_NAME, server.EntryGroupNew()), DBUS_INTERFACE_ENTRY_GROUP)
    for share in parse_shares():
        serviceName = "%s:%s" % (hostname, share)
        serviceTXT = "%s%s" % (serviceTXTPrefix, share)
        group.AddService(IF_UNSPEC, PROTO_INET, UInt32(0), serviceName, serviceType, serviceDomain, hostname, UInt16(servicePort), string_array_to_txt_array([serviceTXT]))
        group.Commit()
# Start the MainLoop for Avahi
main_loop = MainLoop()
main_loop.run()
