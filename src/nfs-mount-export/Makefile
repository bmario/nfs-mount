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
