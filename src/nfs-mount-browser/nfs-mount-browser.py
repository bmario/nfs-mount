#!/usr/bin/python
#
#       nfsmount-browser.py Version 0.1
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

#!/etc/env/python

import dbus, gobject, avahi, os, subprocess
from dbus import DBusException
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

class nfs_browser(dbus.service.Object):
    def __init__(self):
        DBusGMainLoop(set_as_default=True)

        # prepare own dbus interface
        self.session_bus = dbus.SystemBus()
        name = dbus.service.BusName("de.dragon_soft.nfsmount", self.session_bus)
        dbus.service.Object.__init__(self, dbus.SystemBus(), "/de/dragon_soft/nfsmount")

        # prepare avahi
        self.bus = dbus.SystemBus()
        self.server = dbus.Interface( self.bus.get_object(avahi.DBUS_NAME, '/'), 'org.freedesktop.Avahi.Server')
        self.sbrowser = dbus.Interface(self.bus.get_object(avahi.DBUS_NAME, self.server.ServiceBrowserNew(avahi.IF_UNSPEC, avahi.PROTO_INET, "_nfs._tcp", 'local', dbus.UInt32(0))), avahi.DBUS_INTERFACE_SERVICE_BROWSER)
        self.sbrowser.connect_to_signal("ItemNew", self.newItem)
        self.sbrowser.connect_to_signal("ItemRemove", self.removeItem)
        
        self.shares = {}
        self.mounts = []
        
        # prepare mounting
        try:
            os.makedirs(r"/media/nfs")
        except:
            pass

        gobject.MainLoop().run()
        
    @dbus.service.signal(dbus_interface='de.dragon_soft.nfsmount', signature='s')
    def newShare(self, share):
        pass
        
    @dbus.service.signal(dbus_interface='de.dragon_soft.nfsmount', signature='s')        
    def removeShare(self, share):
        pass

    def newItem(self, interface, protocol, name, stype, domain, flags):
        args = self.server.ResolveService(interface, protocol, name, stype, domain, avahi.PROTO_INET, dbus.UInt32(0))

        txt = ''
        for i in args[9][0]:
            txt = "%s%s" % (txt, i)
            
        name = str(name)
        host = str(args[5])
        address = str(args[7])
        port = str(args[8])
        path = txt[5:]
        self.shares[name] = [name, host, address, port, path]
        
        self.newShare(name)
        
    def removeItem(self, interface, protocol, name, stype, domain, flags):
        if self.isShareMounted(name):
            self.unmountShare(name)
        if name in self.shares:
            del self.shares[name]
        self.removeShare(name)

    @dbus.service.method(dbus_interface='de.dragon_soft.nfsmount', in_signature='s', out_signature='as')
    def getShareInfo(self, share):
        return self.shares[share]

    @dbus.service.method(dbus_interface='de.dragon_soft.nfsmount', in_signature='s', out_signature='b')
    def isShareMounted(self, share):
        if share in self.mounts:
            return True
        else:
            return False

    @dbus.service.method(dbus_interface='de.dragon_soft.nfsmount', in_signature='s', out_signature='')
    def mountShare(self, share):
        share = self.getShareInfo(share)
        try:
            os.makedirs(r"/media/nfs/%s%s" % (share[1], share[4].replace("/", "_")))
        except:
            pass
        os.system(r"mount -t nfs %s:%s /media/nfs/%s%s" % (share[2], share[4], share[1], share[4].replace("/", "_")))
        self.mounts.append(share[0])

        self.mountedShare(share[0])
        
    @dbus.service.method(dbus_interface='de.dragon_soft.nfsmount', in_signature='s', out_signature='')
    def unmountShare(self, share):
        share = self.getShareInfo(share)
        os.system(r"umount -l -f /media/nfs/%s%s" % (share[1], share[4].replace("/", "_")))
        os.rmdir(r"/media/nfs/%s%s" % (share[1], share[4].replace("/", "_")))
        self.mounts.remove(share[0])

        self.unmountedShare(share[0])


    @dbus.service.signal(dbus_interface='de.dragon_soft.nfsmount', signature='s')        
    def mountedShare(self, share):
        pass

    @dbus.service.signal(dbus_interface='de.dragon_soft.nfsmount', signature='s')        
    def unmountedShare(self, share):
        pass
        
    @dbus.service.method(dbus_interface='de.dragon_soft.nfsmount', in_signature='', out_signature='as')
    def getShareList(self):
        return self.shares.keys()

    @dbus.service.method(dbus_interface='de.dragon_soft.nfsmount', in_signature='', out_signature='as')
    def getMountList(self):
        return self.mounts
       
    def print_error(*args):
        print 'error_handler'
        print args[0]

if __name__ == "__main__":
    nfs = nfs_browser()

