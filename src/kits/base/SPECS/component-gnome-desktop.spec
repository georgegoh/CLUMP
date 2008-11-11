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

Summary: Component for GNOME Desktop
Name: component-gnome-desktop
Version: 1.2
Release: 1
License: GPLv2
URL: http://www.osgdc.org
Group: System Environment/Base
Vendor: Platform Computing Inc
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Requires: alacarte
Requires: at-spi
Requires: authconfig-gtk
Requires: bitmap-fonts
Requires: bitstream-vera-fonts
Requires: control-center
Requires: dejavu-lgc-fonts
Requires: desktop-backgrounds-basic
Requires: desktop-printing
Requires: dvd+rw-tools
Requires: eog
Requires: esc
Requires: evince
Requires: file-roller
Requires: firstboot
Requires: freeglut
Requires: gdm
Requires: gedit
Requires: glx-utils
Requires: gnome-applets
Requires: gnome-audio
Requires: gnome-backgrounds
Requires: gnome-mag
Requires: gnome-netstatus
Requires: gnome-panel
Requires: gnome-power-manager
Requires: gnome-screensaver
Requires: gnome-session
Requires: gnome-system-monitor
Requires: gnome-terminal
Requires: gnome-themes
Requires: gnome-user-docs
Requires: gnome-utils
Requires: gnome-vfs2-smb
Requires: gnome-volume-manager
Requires: gok
Requires: gtk2-engines
Requires: gtkhtml3
Requires: im-chooser
Requires: krb5-auth-dialog
Requires: liberation-fonts
Requires: linuxwacom
Requires: metacity
Requires: nautilus
Requires: nautilus-cd-burner
Requires: nautilus-open-terminal
Requires: NetworkManager-gnome
Requires: notification-daemon
Requires: openssh-askpass
Requires: orca
Requires: pirut
Requires: policycoreutils-gui
Requires: rhgb
Requires: sabayon-apply
Requires: synaptics
Requires: system-config-date
Requires: system-config-display
Requires: system-config-network
Requires: system-config-printer
Requires: system-config-services
Requires: system-config-soundcard
Requires: system-config-users
Requires: vino
Requires: vnc-server
Requires: xorg-x11-apps
Requires: xorg-x11-drivers
Requires: xorg-x11-fonts-100dpi
Requires: xorg-x11-fonts-75dpi
Requires: xorg-x11-fonts-ISO8859-1-100dpi
Requires: xorg-x11-fonts-ISO8859-1-75dpi
Requires: xorg-x11-fonts-misc
Requires: xorg-x11-fonts-truetype
Requires: xorg-x11-fonts-Type1
Requires: xorg-x11-server-Xorg
Requires: xorg-x11-twm
Requires: xorg-x11-xauth
Requires: xorg-x11-xfs
Requires: xorg-x11-xinit
Requires: xterm
Requires: yelp

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
* Mon Oct 13 2008 Tsai Li Ming <ltsai@osgdc.org> 1.0-1
- Sync with OCS (r1609)
- Initial 1.0 release

