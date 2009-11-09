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
DBusGMainLoop( set_as_default = True )


class NfsMountShare:
    def __init__( self, name, host, address, port, path, version ):
        self.name = name
        self.host = host
        self.address = address
        self.port = port
        self.path = path
        self.version = version

    def getName( self ):
        return self.name

    def getHost( self ):
        return self.host

    def getAddress( self ):
        return self.address

    def getPort( self ):
        return self.port

    def getPath( self ):
        return self.path

    def getVersion( self ):
        return self.version

    def __str__( self ):
        return self.getName()

    def getMountCommand( self ):
        if( self.version == "4" ):
            return r"mount -t nfs4 %s:%s /media/nfs/%s%s" % ( self.address, self.path, self.host, self.path.replace( "/", "_" ) )
        else:
            return r"mount -t nfs %s:%s /media/nfs/%s%s" % ( self.address, self.path, self.host, self.path.replace( "/", "_" ) )

    def getUnmountCommand( self ):
        return r"umount -l -f /media/nfs/%s%s" % ( self.host, self.path.replace( "/", "_" ) )

    def getMountDir( self ):
        return r"/media/nfs/%s%s" % ( self.host, self.path.replace( "/", "_" ) )

class nfs_browser( dbus.service.Object ):
    def __init__( self ):

        # prepare own dbus interface
        self.session_bus = dbus.SystemBus()
        name = dbus.service.BusName( "de.moonlake.nfsmount", self.session_bus )
        dbus.service.Object.__init__( self, dbus.SystemBus(), "/de/moonlake/nfsmount" )

        # prepare avahi
        self.bus = dbus.SystemBus()
        self.server = dbus.Interface( self.bus.get_object( avahi.DBUS_NAME, '/' ), 'org.freedesktop.Avahi.Server' )

        # nfs3 scanning
        self.sbrowser = dbus.Interface( self.bus.get_object( avahi.DBUS_NAME, self.server.ServiceBrowserNew( avahi.IF_UNSPEC, avahi.PROTO_INET, "_nfs._tcp", 'local', dbus.UInt32( 0 ) ) ), avahi.DBUS_INTERFACE_SERVICE_BROWSER )
        self.sbrowser.connect_to_signal( "ItemNew", self.newItem )
        self.sbrowser.connect_to_signal( "ItemRemove", self.removeItem )

        # nfs4 scanning
        self.s4browser = dbus.Interface( self.bus.get_object( avahi.DBUS_NAME, self.server.ServiceBrowserNew( avahi.IF_UNSPEC, avahi.PROTO_INET, "_nfs4._tcp", 'local', dbus.UInt32( 0 ) ) ), avahi.DBUS_INTERFACE_SERVICE_BROWSER )
        self.s4browser.connect_to_signal( "ItemNew", self.newItem )
        self.s4browser.connect_to_signal( "ItemRemove", self.removeItem )


        self.shares = {}
        self.mounts = []

        self.updateMountList()

        # prepare mounting
        try:
            os.makedirs( r"/media/nfs" )
        except:
            pass

        gobject.MainLoop().run()

    def newItem( self, interface, protocol, name, stype, domain, flags ):
        args = self.server.ResolveService( interface, protocol, name, stype, domain, avahi.PROTO_INET, dbus.UInt32( 0 ) )

        txt = ''
        for i in args[9][0]:
            txt = "%s%s" % ( txt, i )

        if( stype == "_nfs4._tcp" ):
            version = "4"
        else:
            version = "3"

        name = str( name )
        host = str( args[5] )
        address = str( args[7] )
        port = str( args[8] )
        path = txt[5:]

        # create new share class and store it
        self.shares[name] = NfsMountShare( name, host, address, port, path, version )

        # emit signal "newShare"
        self.newShare( name )

        # looking for mounts allready done, outside from me
        self.updateMountList()

    def removeItem( self, interface, protocol, name, stype, domain, flags ):
        if self.isShareMounted( name ):
            self.unmountShare( name )
        if name in self.shares:
            del self.shares[name]
        self.removeShare( name )

    @dbus.service.signal( dbus_interface = 'de.moonlake.nfsmount', signature = 's' )
    def newShare( self, share ):
        pass

    @dbus.service.signal( dbus_interface = 'de.moonlake.nfsmount', signature = 's' )
    def removeShare( self, share ):
        pass

    @dbus.service.method( dbus_interface = 'de.moonlake.nfsmount', in_signature = 's', out_signature = 'as' )
    def getShareInfo( self, share ):
        share = self.shares[share]
        return [share.getName(), share.getHost(), share.getAddress(), share.getPort(), share.getPath(), share.getVersion()]

    @dbus.service.method( dbus_interface = 'de.moonlake.nfsmount', in_signature = 's', out_signature = 'b' )
    def isShareMounted( self, share ):
        if share in self.mounts:
            return True
        else:
            return False

    @dbus.service.method( dbus_interface = 'de.moonlake.nfsmount', in_signature = 's', out_signature = '' )
    def mountShare( self, share ):
        try:
            share = self.shares[share]
        except:
            pass
        try:
            os.makedirs( share.getMountDir() )
            os.system( share.getMountCommand() )
        except:
            pass

        self.updateMountList()

    @dbus.service.method( dbus_interface = 'de.moonlake.nfsmount', in_signature = 's', out_signature = '' )
    def unmountShare( self, share ):
        try:
            share = self.shares[share]
        except:
            pass
        try:
            os.system( share.getUnmountCommand() )
            os.rmdir( share.getMountDir() )
        except:
            pass
        self.updateMountList()

    @dbus.service.signal( dbus_interface = 'de.moonlake.nfsmount', signature = 's' )
    def mountedShare( self, share ):
        pass

    @dbus.service.signal( dbus_interface = 'de.moonlake.nfsmount', signature = 's' )
    def unmountedShare( self, share ):
        pass

    @dbus.service.method( dbus_interface = 'de.moonlake.nfsmount', in_signature = '', out_signature = 'as' )
    def getShareList( self ):
        return self.shares.keys()

    @dbus.service.method( dbus_interface = 'de.moonlake.nfsmount', in_signature = '', out_signature = 'as' )
    def getMountList( self ):
        return self.mounts

    @dbus.service.method( dbus_interface = 'de.moonlake.nfsmount', in_signature = '', out_signature = '' )
    def updateMounts( self ):
        self.updateMountList()

    def updateMountList( self, filename = '/etc/mtab' ):
        oldmounts = self.mounts
        self.mounts = []
        f = open( filename, 'r' )
        for line in f.readlines():
            if( line.find( 'nfsd' ) >= 0 ): continue # don't care about nfsd pseudo file system
            if( line.find( ' nfs' ) == -1 ): continue # we just need nfs or nfs4 file systems
            address = line[:line.find( ":" )]
            path = line[line.find( ":" ) + 1:line.find( " " )]

            # iter all shares
            for share in self.shares.itervalues():
                if( share.getAddress() == address and share.getPath() == path ):
                    # mount matches known share
                    self.mounts.append( share.getName() )

                    # if new trigger signal
                    if( share.getName() not in oldmounts ):
                        self.mountedShare( share.getName() )
                    # if share not new, remove it from oldmountlist, so we know, which mounts are unmounted
                    if( share.getName() in oldmounts ):
                        oldmounts.remove( share.getName() )
        f.close()

        for share in oldmounts:
            self.unmountedShare( share )

if __name__ == "__main__":
    nfs = nfs_browser()

