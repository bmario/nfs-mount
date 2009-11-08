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

import gtk
import dbus
import avahi
from sys import exit
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
try:
	import pynotify
except:
	print "You don't seem to have pynotify installed."
	print "So there are no notifications."

class NfsMountSystrayApplet:
	def __init__(self):
		# set icon
		self.icon = gtk.status_icon_new_from_icon_name("server")

		# connect to signals		
		self.icon.connect("popup-menu", self.show_menu)
		self.icon.connect("activate", self.show_shares)

		# dbus stuff
		try:
			bus = dbus.SystemBus()
			self.nfsmount = dbus.Interface(bus.get_object('de.moonlake.nfsmount', '/de/moonlake/nfsmount'), 'de.moonlake.nfsmount')
		except:
			print "Could not connect to the nfs-mount-browser daemon over DBus. Please make sure, that the daemon is running."
			exit(0)

		# set tooltip
		self.update_tooltip()
			
		# connect to dbus signals
		self.nfsmount.connect_to_signal("newShare", self.new_share)
		self.nfsmount.connect_to_signal("removeShare", self.remove_share)
		self.nfsmount.connect_to_signal("mountedShare", self.mounted_share)
		self.nfsmount.connect_to_signal("unmountedShare", self.unmounted_share)

		# initial scan for shares
		for share in self.nfsmount.getShareList():
			self.new_share(share)
		for share in self.nfsmount.getMountList():
			self.mounted_share(share)

		gtk.main()

	# quit methode
	def quit(self,widget,event=None):
		gtk.main_quit()

	# unmount handler
	def unmount_share(self, widget, event=None):
		if event in self.nfsmount.getMountList():
			try:
				self.nfsmount.unmountShare(event)
				self.nfsmount.updateMounts()
			except:
				print "Disconnected from the DBus interface of nfs-mount-browser. Make sure, that this daemon runs."
				exit(0) 
    # mount handler    
	def mount_share(self, widget, event=None):
		if event not in self.nfsmount.getMountList():
			try:
				self.nfsmount.mountShare(event)
				self.nfsmount.updateMounts()
			except:
				print "Disconnected from the DBus interface of nfs-mount-browser. Make sure, that this daemon runs."
				exit(0) 


	def new_share(self, share):
		share = self.nfsmount.getShareInfo(share)
		self.update_tooltip()
		self.notify_user("New Nfs Share Found", "share name: <b>%s</b>\nhost: <b>%s</b>\naddress: <b>%s</b>\npath: <b>%s</b>" % (share[0], share[1], share[2], share[4]))

	def remove_share(self, share):
		self.sharelist.remove(share)
		self.update_tooltip()
		self.notify_user("Nfs Share has been removed", "share name: <b>%s</b>" % share)

	def mounted_share(self, share):
		self.update_tooltip()
		self.notify_user("Nfs Share has been mounted", "share name: <b>%s</b>" % share)

	def unmounted_share(self, share):
		self.update_tooltip()
		self.notify_user("Nfs Share has been unmounted", "share name: <b>%s</b>" % share)


	def update_tooltip(self, message=None):
		tooltip = "Nfs Browser\n%i shares found.\n%i shares mounted." % (len(self.nfsmount.getShareList()), len(self.nfsmount.getMountList()))
		if (message != None):
			tooltip = message + "\n" + tooltip
		self.icon.set_tooltip(tooltip)
		
	def show_menu(self, icon, button, timer):
		self.nfsmount.updateMounts()
		menu = gtk.Menu()
		i = 0
		for share in self.nfsmount.getShareList():
			item = gtk.MenuItem()
			hbox = gtk.HBox(False,12)
			item.add(hbox)
			try:
				si = self.nfsmount.getShareInfo(share)
			except:
				print "Disconnected from the DBus interface of nfs-mount-browser. Make sure, that this daemon runs."
				exit(0) 
				
			if share in self.nfsmount.getMountList():
				hbox.pack_start(gtk.image_new_from_stock(gtk.STOCK_CONNECT,gtk.ICON_SIZE_MENU),False,False)
				item.connect("activate",self.unmount_share, share)
				tooltip = "Hostname: %s\nAddress: %s\nPath: %s\nVersion: %s\nShare is mounted." % (si[1], si[2],si[4], si[5])
			else:
				hbox.pack_start(gtk.image_new_from_stock(gtk.STOCK_DISCONNECT,gtk.ICON_SIZE_MENU),False,False)
				item.connect("activate",self.mount_share, share)
				tooltip = "Hostname: %s\nAddress: %s\nPath: %s\nVersion: %s\nShare is not mounted" % (si[1], si[2], si[4],si[5])
			label = gtk.Label(share)
			label.set_alignment(1,1)
			hbox.pack_start(label,False,False)
			info = gtk.image_new_from_stock(gtk.STOCK_INFO,gtk.ICON_SIZE_MENU)
			info.set_tooltip_text(tooltip)
			info.set_alignment(1,1)
			hbox.pack_start(info,True,True)			
			menu.attach(item,0,1,i,i+1)
			i = i + 1
		menu.attach(gtk.MenuItem(),0,1,i,i+1)			
		i = i + 1
		item = gtk.MenuItem()
		item.connect("activate",self.quit)
		hbox = gtk.HBox(False,12)
		item.add(hbox)
		hbox.pack_start(gtk.image_new_from_stock(gtk.STOCK_QUIT,gtk.ICON_SIZE_MENU),False,False)
		label = gtk.Label("Quit")
		hbox.pack_start(label,False,False)
		menu.attach(item,0,1,i,i+1)
		
			
		menu.show_all()
		menu.popup(None, None, gtk.status_icon_position_menu, button, timer, icon)
		self.update_tooltip()
		
	def show_shares(self, icon):
		self.update_tooltip()		

	def notify_user(self, title, message):
		try:
			# use pynotify or nothing!
			pynotify.init("Nfs Browser")
			notification = pynotify.Notification(title, message, "server")
			#notification.attach_to_status_icon(self.icon)
			notification.show()
		except:
			pass
		
run = NfsMountSystrayApplet()

