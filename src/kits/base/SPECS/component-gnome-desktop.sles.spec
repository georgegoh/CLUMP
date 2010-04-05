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
# $Id: component-gnome-desktop.sles.spec 3135 2009-10-23 05:42:58Z ltsai $
# 

Summary: Component for GNOME Desktop
Name: component-gnome-desktop
Version: 2.0
Release: 1
Epoch: 1
License: GPLv2
URL: http://www.osgdc.org
Group: System Environment/Base
Vendor: Platform Computing Inc
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot

Requires: xterm MozillaFirefox mozilla-xulrunner yast2-qt yast2-x11 gnome-panel-nld gnome-main-menu
Requires: cups-backends ifnteuro desktop-data-NLD bitstream-vera libcroco libglade2 libgtop
Requires: libmusicbrainz libraw1394 libsvg lzo openssh-askpass sax2-ident susehelp_en
Requires: unclutter x11-input-synaptics xkeyboard-config xorg-x11-fonts-100dpi xterm dbus-1
Requires: fam-server gdk-pixbuf imlib libgnomeprint libvorbis poppler xdg-menu gail fvwm2
Requires: kdelibs3 libsndfile qt-x11 yast2-sound gnome2-NLD xorg-x11-driver-video-radeon
Requires: python-gtk libgda sax2-libsax evolution-data-server xorg-x11-driver-video-nvidia
Requires: jack gnome-terminal gnome-keyring-manager  gnome-cups-manager mozilla-xulrunner
Requires: gnome-power-manager gal2 librsvg file-roller nautilus-share gnome-media
Requires: gnome-applets yast2-control-center dbus-1-x11 ghostscript-fonts-other
Requires: aalib dejavu dialog gle gtk2-engines fonts-config cabextract gnome-audio fribidi
Requires: info2html iso-codes gnome-mime-data guile dosbootdisk hplip-hpijs intlfnts dmapi
Requires: htdig ghostscript-fonts-std latex2html-pngicons libcddb libdaemon libgimpprint
Requires: libgnomecups libidl libiniparser libnetpbm libopencdk libsamplerate
Requires: libstroke libwnck lsb mDNSResponder-lib ncpfs poppler qt startup-notification
Requires: sax2-tools taglib thinkeramik-style unrar vte x11-tools xdmbgrd xli xorg-x11-Xvnc
Requires: xorg-x11-fonts-75dpi xorg-x11-server-glx xtermset gnome-printer-add evms-gui alsa
Requires: gnome-themes gnutls gtk-sharp2 ghostscript-library libgnomecanvas libsexy libtheora
Requires: mozilla-nss orbit2 qt-sql tightvnc xorg-x11 gmime gtksourceview ghostscript-x11
Requires: esound gconf2 input-utils libbonobo libsoup python-orbit samba xorg-x11-server
Requires: zen-updater gnome-doc-utils gnome-nettool gnome-vfs2 libao notification-daemon
Requires: qt-qt3support xlockmore gstreamer010-plugins-base gnome-menus libgnome libnotify
Requires: xorg-x11-driver-video gstreamer010-plugins-good libbonoboui sax2-libsax-perl
Requires: MozillaFirefox-translations yast2-x11 gconf-editor gcalctool gnome-spell2
Requires: gnome-system-monitor libgnomedb libssui python-gnome hal-gnome gnome-desktop eel
Requires: evince gdm nautilus control-center2 nautilus-open-terminal system-tools-backends
Requires: eog gnome-panel-nld gnome-session gnome-utils yast2-control-center-gnome susehelp
Requires: 3ddiag OpenEXR agfa-fonts freeglut fam gstreamer010 gnome2-user-docs gtk cifs-mount
Requires: desktop-file-utils efont-unicode cdrecord libbeagle libexif libgsf libjasper
Requires: libogg libsmbclient libxklavier mozilla-nspr python-numeric shared-mime-info
Requires: tango-icon-theme vcdimager xaw3d xorg-x11-Xnest xorg-x11-fonts-scalable yast2-qt
Requires: SDL gtk2-themes flac libcdio libsvg-cairo netpbm samba-client xscreensaver gtkspell
Requires: awesfx gtk-engines python-cairo sox zenity at-spi metacity sax2 cdrdao libgsf-gnome
Requires: MozillaFirefox sax2-gui libgnomeui gnome-screensaver gucharmap libgnomesu vino
Requires: libgnomeprintui gtkhtml2 gedit nautilus-cd-burner gnome-volume-manager
Requires: gnome-main-menu yelp

%description
This component provides the GNOME Desktop environment for installers.

%prep

%build

%install
rm -rf $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files

%pre

%post
#equivalent of post section

%preun

%postun
#equivalent of uninstall section

%changelog
* Tue Jun 16 2009 Chew Meng Kuan <mkchew@platform.com> 5.3-1
- Bump version to 5.3 for PCM 1.2.1.

* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

