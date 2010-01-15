#!/usr/bin/python
#
#       nfs-mount-systray.py Version 0.2
#
#       Copyright 2008 2009 2010 Mario Bielert <mario@moonlake.de>
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

import gtk
import gconf
import dbus
import avahi
from sys import exit
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop( set_as_default = True )
try:
    import pynotify
except:
    print "You don't seem to have pynotify installed."
    print "So there are no bubble notifications."
    print "To change this, just install python-notify."

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

class NfsMountSystrayApplet:
    def __init__( self ):
        # set notification
        self.load_notify_conf()

        # set icon
        self.icon = gtk.status_icon_new_from_icon_name( "server" )

        # connect to signals        
        self.icon.connect( "popup-menu", self.show_menu )
        self.icon.connect( "activate", self.show_shares )

        # dbus stuff
        try:
            bus = dbus.SystemBus()
            self.nfsmount = dbus.Interface( bus.get_object( 'de.moonlake.nfsmount', '/de/moonlake/nfsmount' ), 'de.moonlake.nfsmount' )
        except:
            self.connectDBus()

        # set tooltip
        self.update_tooltip()

        # connect to dbus signals
        self.nfsmount.connect_to_signal( "newShare", self.new_share )
        self.nfsmount.connect_to_signal( "removeShare", self.remove_share )
        self.nfsmount.connect_to_signal( "mountedShare", self.mounted_share )
        self.nfsmount.connect_to_signal( "unmountedShare", self.unmounted_share )
        self.nfsmount.connect_to_signal( "mountError", self.mount_error )
        self.nfsmount.connect_to_signal( "unmountError", self.unmount_error )

        # initial scan for shares
        for share in self.nfsmount.getShareList():
            self.new_share( share )
        for share in self.nfsmount.getMountList():
            self.mounted_share( share )

        gtk.main()

    def load_notify_conf( self ):
        client = gconf.client_get_default()
        client.add_dir( '/apps/nfs-mount-systray/notifications', gconf.CLIENT_PRELOAD_NONE )
        client.add_dir( '/apps/nfs-mount-systray/shares', gconf.CLIENT_PRELOAD_NONE )
        # first run?
        if( client.get_bool( '/apps/nfs-mount-systray/init' ) == 0 ):
            # set standard values
            client.set_bool( '/apps/nfs-mount-systray/notifications/all', 1 )
            client.set_bool( '/apps/nfs-mount-systray/publishing', 1 )
            client.set_bool( '/apps/nfs-mount-systray/init', 1 )
            self.notify = True
        else:
            # load old value
            self.notify = client.get_bool( '/apps/nfs-mount-systray/notifications/all' )
            self.publishing = client.get_bool( '/apps/nfs-mount-systray/publishing' )

    # unmount handler
    def unmount_share( self, widget, event = None ):
        if event in self.nfsmount.getMountList():
            try:
                self.nfsmount.unmountShare( event )
            except:
                self.connectDBus()

    # mount handler    
    def mount_share( self, widget, event = None ):
        if event not in self.nfsmount.getMountList():
            self.nfsmount.mountShare( event )

            #except:
            #    self.connectDBus()


    # mount error handler
    def mount_error( self, share ):
        self.notify_user_error( "Nfs Share could not be mounted", "share name: <b>%s</b>" % share )

    # unmount error handler
    def unmount_error( self, share ):
        self.notify_user_error( "Nfs Share could not be unmounted", "share name: <b>%s</b>" % share )

    def new_share( self, share ):
        share = self.nfsmount.getShareInfo( share )

        self.update_tooltip()
        self.notify_user( "New Nfs Share Found", "share name: <b>%s</b>\nhost: <b>%s</b>\naddress: <b>%s</b>\npath: <b>%s</b>" % ( share[0], share[1], share[2], share[4] ) )

        client = gconf.client_get_default()
        client.add_dir( '/apps/nfs-mount-systray/shares/%s' % share[0].replace( "/", "_" ), gconf.CLIENT_PRELOAD_NONE )
        if client.get_bool( '/apps/nfs-mount-systray/shares/%s/automount' % share[0].replace( "/", "_" ) ) == 1:
            self.nfsmount.mountShare( share[0] )
        else:
            client.set_bool( '/apps/nfs-mount-systray/shares/%s/automount' % share[0].replace( "/", "_" ), 0 )

    def remove_share( self, share ):
        self.update_tooltip()
        self.notify_user( "Nfs Share has been removed", "share name: <b>%s</b>" % share )

    def mounted_share( self, share ):
        self.update_tooltip()
        self.notify_user( "Nfs Share has been mounted", "share name: <b>%s</b>" % share )

    def unmounted_share( self, share ):
        self.update_tooltip()
        self.notify_user( "Nfs Share has been unmounted", "share name: <b>%s</b>" % share )


    def update_tooltip( self ):
        tooltip = "Nfs Browser\n%i shares found.\n%i shares mounted." % ( len( self.nfsmount.getShareList() ), len( self.nfsmount.getMountList() ) )
        self.icon.set_tooltip( tooltip )

    def show_menu( self, icon, button, timer ):
        try:
            self.nfsmount.updateMounts()
        except:
            self.connectDBus()

        menu = gtk.Menu()
        i = 0
        for share in self.nfsmount.getShareList():
            item = gtk.MenuItem()
            hbox = gtk.HBox( False, 12 )
            item.add( hbox )
            try:
                si = self.nfsmount.getShareInfo( share )
                share = NfsMountShare( si[0], si[1], si[2], si[3], si[4], si[5] )
            except:
                print "Could not connect to the nfs-mount-browser daemon over DBus. Please make sure, that the daemon is running."
                exit( 0 )

            if share.getName() in self.nfsmount.getMountList():
                hbox.pack_start( gtk.image_new_from_stock( gtk.STOCK_CONNECT, gtk.ICON_SIZE_MENU ), False, False )
                item.connect( "activate", self.unmount_share, share.getName() )
                tooltip = "Hostname: %s\nAddress: %s\nPath: %s\nVersion: %s\nShare is mounted." % ( share.getHost(), share.getAddress(), share.getPath(), share.getVersion() )
            else:
                hbox.pack_start( gtk.image_new_from_stock( gtk.STOCK_DISCONNECT, gtk.ICON_SIZE_MENU ), False, False )
                item.connect( "activate", self.mount_share, share.getName() )
                tooltip = "Hostname: %s\nAddress: %s\nPath: %s\nVersion: %s\nShare is not mounted" % ( share.getHost(), share.getAddress(), share.getPath(), share.getVersion() )
            label = gtk.Label( share.getName() )
            label.set_alignment( 1, 1 )
            hbox.pack_start( label, False, False )
            info = gtk.image_new_from_stock( gtk.STOCK_INFO, gtk.ICON_SIZE_MENU )
            info.set_tooltip_text( tooltip )
            info.set_alignment( 1, 1 )
            hbox.pack_end( info )
            menu.attach( item, 0, 1, i, i + 1 )
            i = i + 1
        if i > 0:
            menu.attach( gtk.SeparatorMenuItem(), 0, 1, i, i + 1 )

        # avahi publishing switch
        i = i + 1
        item = gtk.CheckMenuItem( "Publish own shares" )
        item.set_active( self.publishing )
        item.connect( "activate", self.toggle_publishing )
        item.set_tooltip_text( "Enables publishing own shares to other using the Avahi framework." )
        menu.attach( item, 0, 1, i, i + 1 )

        # notification switch
        i = i + 1
        item = gtk.CheckMenuItem( "Notifications" )
        item.set_active( self.notify )
        item.connect( "activate", self.toggle_notify )
        item.set_tooltip_text( "Enable notification if there is an event." )
        menu.attach( item, 0, 1, i, i + 1 )

        # quit button
        i = i + 1
        item = gtk.ImageMenuItem( gtk.STOCK_QUIT )
        item.connect( "activate", self.quit )
        item.set_tooltip_text( "Quit the applet." )
        menu.attach( item, 0, 1, i, i + 1 )


        menu.show_all()
        menu.popup( None, None, gtk.status_icon_position_menu, button, timer, icon )
        self.update_tooltip()

    def connectDBus( self ):
        self.notify_user_error( "DBus Connection Error", "Could not connect to the nfs-mount-browser daemon over DBus. Please make sure, that this daemon is running. And then restart the applet." )

        exit( 0 )

    # quit methode
    def quit( self, widget, event = None ):
        gtk.main_quit()

    # toggle notifications
    def toggle_notify( self, widget, event = None ):
        client = gconf.client_get_default()
        self.notify = not self.notify
        if( self.notify ):
            client.set_bool( '/apps/nfs-mount-systray/notifications/all', 1 )
        else:
            client.set_bool( '/apps/nfs-mount-systray/notifications/all', 0 )

    # toggle publishing
    def toggle_publishing( self, widget, event = None ):
        client = gconf.client_get_default()
        self.publishing = not self.publishing
        if( self.publishing ):
            client.set_bool( '/apps/nfs-mount-systray/publishing', 1 )
            self.nfsmount.publishShares()
        else:
            client.set_bool( '/apps/nfs-mount-systray/publishing', 0 )
            self.nfsmount.unpublishShares()


    def show_shares( self, icon ):
        self.icon.set_blinking( False )
        self.update_tooltip()

    def notify_user_error( self, title, message ):
        # print to console
        print "%s:\n%s" % ( title, message )

        try:
            # use pynotify or nothing!
            pynotify.init( "Nfs Browser" )
            notification = pynotify.Notification( title, message, "server" )
            notification.set_urgency( pynotify.URGENCY_CRITICAL )
            notification.show()
        except:
            # there is no libnotify :( lets blink!
            self.icon.set_blinking( True )

            # update tooltip, maybe somebody reads :)
            tooltip = "Nfs Browser\n%s:\n%s" % ( title, message )
            self.icon.set_tooltip( tooltip )

    def notify_user( self, title, message ):
        if self.notify:
            # notify me :)
            try:
                # use pynotify or nothing!
                pynotify.init( "Nfs Browser" )
                notification = pynotify.Notification( title, message, "server" )
                #notification.attach_to_status_icon(self.icon)
                notification.show()
            except:
                # there is no libnotify :( lets blink!
                self.icon.set_blinking( True )

                # update tooltip, maybe somebody reads :)
                tooltip = "Nfs Browser\n%s:\n%s" % ( title, message )
                self.icon.set_tooltip( tooltip )

                # print to console
                print title, message

        else:
            # no notifications pls!
            pass

run = NfsMountSystrayApplet()
