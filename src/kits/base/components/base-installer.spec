# Copyright (C) 2007 Platform Computing Inc
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
# 
# $Id$
# 

Summary: Component for Kusu Installer Base
Name: component-base-installer
Version: 0.1
Release: 0
License: GPLv2
Group: System Environment/Base
Vendor: Platform Computing Inc
BuildArchitectures: noarch
Requires: kusu-base-installer 
Requires: kusu-base-node 
Requires: kusu-boot
Requires: kusu-buildkit 
Requires: kusu-core 
Requires: kusu-driverpatch 
Requires: kusu-hardware 
Requires: kusu-kitops 
Requires: kusu-networktool 
Requires: kusu-path 
Requires: kusu-partitiontool 
Requires: kusu-repoman 
Requires: kusu-sqlalchemy 
Requires: kusu-ui 
Requires: kusu-util 
Requires: kusu-nodeinstaller-patchfiles 
Requires: mysql
Requires: mysql-server
Requires: dhcp
Requires: xinetd
Requires: tftp-server
Requires: syslinux
Requires: httpd
Requires: python
Requires: python-devel
Requires: MySQL-python
Requires: createrepo
Requires: rsync
Requires: bind
Requires: caching-nameserver
Requires: pdsh
Requires: pdsh-rcmd-exec
Requires: pdsh-rcmd-rsh
Requires: pdsh-rcmd-ssh
Requires: pdsh-mod-machines
Requires: pdsh-mod-dshgroup
Requires: pdsh-mod-netgroup
Requires: pdsh-debuginfo
Requires: modules
Requires: kusu-cheetah
Requires: kusu-pysqlite
Requires: kusu-ipy
Requires: initrd-templates
Requires: pyparted
Requires: rsh
# For GNOME Desktop Environment - START
Requires: NetworkManager-gnome
Requires: alacarte
Requires: at-spi
Requires: beagle-evolution
Requires: beagle-gui
Requires: compiz
Requires: control-center
Requires: desktop-printing
Requires: dvd+rw-tools
Requires: eog
Requires: esc
Requires: evince
Requires: file-roller
Requires: gedit
Requires: gimp-print-utils
Requires: gnome-applets
Requires: gnome-audio
Requires: gnome-backgrounds
Requires: gnome-bluetooth
Requires: gnome-media
Requires: gnome-netstatus
Requires: gnome-panel
Requires: gnome-pilot
Requires: gnome-power-manager
Requires: gnome-screensaver
Requires: gnome-session
Requires: gnome-system-monitor
Requires: gnome-terminal
Requires: gnome-themes
Requires: gnome-user-docs
Requires: gnome-user-share
Requires: gnome-utils
Requires: gnome-vfs2-smb
Requires: gnome-volume-manager
Requires: gok
Requires: gthumb
Requires: gtk2-engines
Requires: im-chooser
Requires: metacity
Requires: nautilus
Requires: nautilus-cd-burner
Requires: nautilus-sendto
Requires: nautilus-sendto-bluetooth
Requires: notification-daemon
Requires: orca
Requires: tomboy
Requires: vino
Requires: yelp
Requires: NetworkManager-glib
Requires: PyXML
Requires: alsa-lib
Requires: audiofile
Requires: avahi
Requires: avahi-glib
Requires: beagle
Requires: brlapi
Requires: cdparanoia-libs
Requires: cdrdao
Requires: cdrecord
Requires: chkfontpath
Requires: cpp
Requires: dbus-x11
Requires: desktop-backgrounds-basic
Requires: docbook-dtds
Requires: eel2
Requires: esound
Requires: evolution
Requires: evolution-data-server
Requires: evolution-sharp
Requires: festival
Requires: firefox
Requires: flac
Requires: foomatic
Requires: gail
Requires: gamin
Requires: gcalctool
Requires: ghostscript
Requires: ghostscript-fonts
Requires: giflib
Requires: gimp-print
Requires: gmime
Requires: gmime-sharp
Requires: gnome-bluetooth-libs
Requires: gnome-desktop
Requires: gnome-doc-utils
Requires: gnome-icon-theme
Requires: gnome-keyring
Requires: gnome-mag
Requires: gnome-menus
Requires: gnome-mime-data
Requires: gnome-mount
Requires: gnome-python2
Requires: gnome-python2-applet
Requires: gnome-python2-bonobo
Requires: gnome-python2-desktop
Requires: gnome-python2-extras
Requires: gnome-python2-gconf
Requires: gnome-python2-gnomeprint
Requires: gnome-python2-gnomevfs
Requires: gnome-python2-gtksourceview
Requires: gnome-python2-libegg
Requires: gnome-sharp
Requires: gnome-speech
Requires: gnome-spell
Requires: gnome-vfs2
Requires: gphoto2
Requires: gsf-sharp
Requires: gstreamer
Requires: gstreamer-plugins-base
Requires: gstreamer-plugins-good
Requires: gstreamer-tools
Requires: gtk-sharp2
Requires: gtkhtml3
Requires: gtksourceview
Requires: gtkspell
Requires: gucharmap
Requires: hal-cups-utils
Requires: hicolor-icon-theme
Requires: httpd
Requires: libFS
Requires: libXScrnSaver
Requires: libXTrap
Requires: libXaw
Requires: libXcomposite
Requires: libXdamage
Requires: libXevie
Requires: libXfont
Requires: libXfontcache
Requires: libXmu
Requires: libXpm
Requires: libXres
Requires: libXtst
Requires: libXv
Requires: libXxf86dga
Requires: libXxf86misc
Requires: libart_lgpl
Requires: libavc1394
Requires: libbeagle
Requires: libbonobo
Requires: libbonoboui
Requires: libbtctl
Requires: libcroco
Requires: libdaemon
Requires: libdmx
Requires: libdv
Requires: libexif
Requires: libfontenc
Requires: libgail-gnome
Requires: libgdiplus
Requires: libgnome
Requires: libgnomecanvas
Requires: libgnomecups
Requires: libgnomeprint22
Requires: libgnomeprintui22
Requires: libgnomeui
Requires: libgsf
Requires: libgtop2
Requires: libiec61883
Requires: libnotify
Requires: libogg
Requires: liboil
Requires: libraw1394
Requires: librsvg2
Requires: libsoup
Requires: libtheora
Requires: libvorbis
Requires: libwnck
Requires: libxkbfile
Requires: libxklavier
Requires: libxslt
Requires: lockdev
Requires: mkisofs
Requires: mono-core
Requires: mono-data
Requires: mono-data-sqlite
Requires: mono-web
Requires: nautilus-extensions
Requires: openjade
Requires: openobex
Requires: opensp
Requires: perl-Archive-Tar
Requires: perl-Compress-Zlib
Requires: perl-Digest-HMAC
Requires: perl-Digest-SHA1
Requires: perl-HTML-Parser
Requires: perl-HTML-Tagset
Requires: perl-IO-Socket-INET6
Requires: perl-IO-Socket-SSL
Requires: perl-IO-Zlib
Requires: perl-Net-DNS
Requires: perl-Net-IP
Requires: perl-Net-SSLeay
Requires: perl-Socket6
Requires: perl-libwww-perl
Requires: pilot-link
Requires: pkgconfig
Requires: poppler
Requires: poppler-utils
Requires: pycairo
Requires: pygtk2
Requires: pyorbit
Requires: python-numeric
Requires: redhat-artwork
Requires: samba-common
Requires: scrollkeeper
Requires: sgml-common
Requires: shared-mime-info
Requires: spamassassin
Requires: speex
Requires: startup-notification
Requires: system-config-printer-libs
Requires: ttmkfdir
Requires: urw-fonts
Requires: vte
Requires: xkeyboard-config
Requires: xml-common
Requires: xorg-x11-drv-evdev
Requires: xorg-x11-drv-keyboard
Requires: xorg-x11-drv-mouse
Requires: xorg-x11-drv-vesa
Requires: xorg-x11-drv-void
Requires: xorg-x11-font-utils
Requires: xorg-x11-fonts-base
Requires: xorg-x11-server-Xorg
Requires: xorg-x11-server-utils
Requires: xorg-x11-utils
Requires: xorg-x11-xauth
Requires: xorg-x11-xfs
Requires: xorg-x11-xinit
Requires: xorg-x11-xkb-utils
Requires: zenity
Requires: cairo
Requires: dbus
Requires: libxml2
Requires: libxml2-python
Requires: system-config-display
# For GNOME Desktop Environment - END

%description
This component provides the node with the Kusu management tools for the 
installers.

%prep

%files

%pre

%post
#equivalent of post section

%preun

%postun
#equivalent of uninstall section
