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

all:

clean:

install:
	cp nfs-mount-export /etc/init.d/nfs-mount-export
	chmod +x /etc/init.d/nfs-mount-export
	cp nfs-mount-export.py /usr/local/sbin/nfs-mount-export.py
	chmod +x /usr/local/sbin/nfs-mount-export.py
	update-rc.d nfs-mount-export defaults 90
	
uninstall:
	rm /etc/init.d/nfs-mount-export
	rm /usr/local/sbin/nfs-mount-export.py

	update-rc.d nfs-mount-export remove
