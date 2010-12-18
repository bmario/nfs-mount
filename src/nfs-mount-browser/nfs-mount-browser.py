#!/usr/bin/python
#
#       Copyright 2008 2009 2010 Mario Bielert <mario.bielert@googlemail.com>
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
from dbus import SystemBus, Interface, UInt32, UInt16
from avahi import DBUS_NAME, DBUS_PATH_SERVER, DBUS_INTERFACE_ENTRY_GROUP, DBUS_INTERFACE_SERVER, IF_UNSPEC, PROTO_INET, string_array_to_txt_array
from dbus import DBusException
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop( set_as_default = True )

serviceType3 = "_nfs._tcp" # See http://www.dns-sd.org/ServiceTypes.html
serviceType = serviceType3
serviceType4 = "_nfs4._tcp" # This is not Standard, but what else we can do :(
servicePort = 2049        # default NFS port
serviceTXTPrefix = "path="      # TXT record for the service
serviceDomain = "local"

serviceRootPath = None

class NfsAvahiPublish:
    def __init__( self ):
        # prepare avahi binding
        bus = SystemBus()
        server = Interface( 
                bus.get_object( DBUS_NAME, DBUS_PATH_SERVER ),
                DBUS_INTERFACE_SERVER )
        self.hostname = server.GetHostNameFqdn()
        self.group = Interface( bus.get_object( DBUS_NAME, server.EntryGroupNew() ), DBUS_INTERFACE_ENTRY_GROUP )

        self.export()

    # exports every share on this host  
    def export( self ):
        self.unexport()
        not_empty = False
        for share in self.parse_shares():
            # export the shares
            self.export_share( share )
            not_empty = True
        if not_empty:
            self.group.Commit()

    def unexport( self ):
        self.group.Reset()

    def detect_nfs_version( self, filename = '/etc/exports' ):
        """
        Parses filename and detect the version of the used nfs
        
        Returns: 3, 4
        """
        global serviceRootPath, serviceType, serviceType4

        try:
            f = open( filename, 'r' )
        except:
            return 3
		
        for line in f.readlines():
            try:
                if line.strip()[0] == '#': continue
                if line.find( 'fsid=0' ) >= 0:
                    normalized_line = line.strip().replace( '\t', '    ' )
                    serviceRootPath = normalized_line.split()[0]
                    serviceType = serviceType4
                    return 4
            except:
                pass

        f.close()
        return 3

    def parse_shares( self, filename = '/etc/exports' ):
        """
        Parses NFS Shares from filename.
    
        Returns: List of Shares
        """
        global serviceRootPath

        version = self.detect_nfs_version()
        shares = []
        try:
            f = open( filename, 'r' )
        except:
            return []
            
        for line in f.readlines():
            try: # try is used for empty lines
                if line.strip()[0] == '#': continue # is it a comment?

                normalized_line = line.strip().replace( '\t', '    ' )
                path = normalized_line.split()[0] #normalized path

                # nfs4 stuff
                if( version == 4 ):
                    path = path.replace( serviceRootPath, '' )
                    if path.strip() == '': path = '/'

                shares.append( path )
            except:
                pass

        f.close()

        return shares


    def export_share( self, share ):

        serviceName = "%s:%s" % ( self.hostname, share )
        serviceTXT = "%s%s" % ( serviceTXTPrefix, share )
        self.group.AddService( IF_UNSPEC, PROTO_INET, UInt32( 0 ), serviceName, serviceType, serviceDomain, self.hostname, UInt16( servicePort ), string_array_to_txt_array( [serviceTXT] ) )

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

        # prepare avahi publish
        self.publish = NfsAvahiPublish()
        self.publish.export()

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
    def mountError( self, share ):
        pass

    @dbus.service.signal( dbus_interface = 'de.moonlake.nfsmount', signature = 's' )
    def unmountError( self, share ):
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
        except:
            pass

        try:
            os.system( share.getMountCommand() )
        except:
            os.rmdir( share.getMountDir )

        self.updateMountList()

        if share.getName() not in self.mounts:
            self.mountError( share.getName() )


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

        if share.getName() in self.mounts:
            self.unmountError( share.getName() )

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

    @dbus.service.method( dbus_interface = 'de.moonlake.nfsmount', in_signature = '', out_signature = '' )
    def publishShares( self ):
        self.publish.export()

    @dbus.service.method( dbus_interface = 'de.moonlake.nfsmount', in_signature = '', out_signature = '' )
    def unpublishShares( self ):
        self.publish.unexport()


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
