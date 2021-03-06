#!/usr/bin/python
# -*- coding: utf-8 -*-
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

from dbus import SystemBus, Interface, UInt32, UInt16
from avahi import DBUS_NAME, DBUS_PATH_SERVER, DBUS_INTERFACE_ENTRY_GROUP, DBUS_INTERFACE_SERVER, IF_UNSPEC, PROTO_INET, string_array_to_txt_array
from gobject import MainLoop
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

# We are a Script, lets go!
if __name__ == '__main__':
    # prepare publish
    avahi = NfsAvahiPublish()
    avahi.export()

    # Start the MainLoop for Avahi
    main_loop = MainLoop()
    main_loop.run()#!/usr/bin/python
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
from avahi import DBUS_NAME, DBUS_PATH_SERVER, DBUS_INTERFACE_ENTRY_GROUP, DBUS_INTERFACE_SERVER, IF_UNSPEC, PROTO_INET, string_array_to_txt_array
from gobject import MainLoop
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
        for share in self.parse_shares():
            # export the shares
            self.export_share( share )
        self.group.Commit()

    def unexport( self ):
        self.group.Reset()

    def detect_nfs_version( self, filename = '/etc/exports' ):
        """
        Parses filename and detect the version of the used nfs
        
        Returns: 3, 4
        """
        global serviceRootPath, serviceType, serviceType4

        f = open( filename, 'r' )
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
        f = open( filename, 'r' )
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

# We are a Script, lets go!
if __name__ == '__main__':
    # prepare publish
    avahi = NfsAvahiPublish()
    avahi.export()

    # Start the MainLoop for Avahi
    main_loop = MainLoop()
    main_loop.run()
