��    @        Y         �     �     �  ;   �     �     �          "     4  C   I  &   �     �  %   �     �               (  (   4  (   ]  ;   �     �     �     �     �               .     C     Y     g     �     �     �  $   �  '   �     	     "	     3	     H	     \	     p	     ~	     �	     �	     �	     �	  )   �	  #   
  ,   1
      ^
  (   
     �
     �
     �
  +   �
          $     5     G     Z     n     �     �     �  K  �            ;   7  D   s  W   �  "        3     E  C   e  &   �     �  %   �     
            .     O  (   \  (   �  ;   �     �  +   �  $     7   @  4   x  0   �     �     �  i       y     �     �  ;   �  ?     9   E  �    �   U  �   �  e   �  a   �  �  K  :   �!  �   "  �   �"  �   ~#  �   t$  ;   
%  5   F%  K   |%     �%  ?   �%     (&     G&  ?   W&  Q   �&  !   �&     '  )   !'  /   K'     {'     �'     �'     �'     �'                 &       @           <   2   0   ,   %          #                  )      9           =      *   !   :       +   1      /                           
         >                     7              .         3       ;            4       5   '           -   8      $      ?         "         (      6          	       Adding script: %s
 Chroot'ing to run script(s)
 Compressing Image.  This will take some time.  Please wait
 DB_Query_Error
 DB_Query_Error: %s
 DB_Update_Error
 Display tool help Display tool version ERROR: Unable to locate kernel package in: %s  Try running:  ls %s
 ERROR: Unknown kernel package type: %s Extracting modules
 Extracting template Initial Ram Disk
 Patching in modules:
 Removing: %s
 Unknown arguments %i
 Version %s
 WARNING:  The base kit is not installed
 WARNING: Unable to locate module(s): %s
 WARNING: Unable to use System.map to verify module symbols
 Winky addhost_Help addhost_interface_usage addhost_macfile_usage addhost_nodegroup_usage addhost_rank_usage addhost_remove_usage addhost_version_usage boothost_Help boothost_no_such_host %s
 boothost_no_such_nodegroup %s
 boothost_reboot boothost_root_reboot boothost_unable_to_get_nodegroup %s
 boothost_unable_to_update_nodegroup %s
 buildimage_Help buildinitrd_Help dbreport_Apache_Help dbreport_Debug_Help dbreport_Dhcpd_Help dbreport_Help dbreport_Hosts_Help dbreport_Named_Help dbreport_Nodes_Help dbreport_Reverse_Help dbreport_Zone_Help dbreport_cannot_determine_DNS_forwarders
 dbreport_cannot_determine_DNS_zone
 dbreport_cannot_determine_primary_installer
 dbreport_cannot_find_plugin: %s
 dbreport_provide_database_user_password
 exit_addhost_instructions exit_addhost_title instruction_node_group kitops: Exactly one kit operation expected
 kitops_Help kitops_usage_add kitops_usage_list kitops_usage_media kitops_usage_remove kitops_usage_upgrade nodeboot_no_hostname_or_ip
 repoman_Help sel_node_group Project-Id-Version: OCS 5.0
Report-Msgid-Bugs-To: support@platform.com
POT-Creation-Date: 2007-03-13 12:06-0400
PO-Revision-Date: 2007-03-13 12:25-0400
Last-Translator: Mark Black <Yah-Right@platform.com>
Language-Team: LANGUAGE <LL@li.org>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
 Adding script: %s
 Chroot'ing to run script(s)
 Compressing Image.  This will take some time.  Please wait
 ERROR:  Database query failed!  Make sure the database is available
 ERROR:  Database query failed!  Make sure the database is available
Failed running: %s
 ERROR:  Unable to update database
 Display tool help Display the version of the tool ERROR: Unable to locate kernel package in: %s  Try running:  ls %s
 ERROR: Unknown kernel package type: %s Extracting modules
 Extracting template Initial Ram Disk
 Patching in modules:
 Removing: %s
 ERROR:  Unknown argument(s): %s
 Version: %s
 WARNING:  The base kit is not installed
 WARNING: Unable to locate module(s): %s
 WARNING: Unable to use System.map to verify module symbols
 Nodd FIXME: addhost_Help Needs to be translated! Set the interface to provide DHCP on Use the following file as the source of the MAC address Set the node group of the hosts that are to be added The rack number to assign the hosts to (if used) Remove the list of hosts Display version of tool boothost [-h|-v|-l {nodename}]
boothost [-t node_group] | [-n node_list] | [-s node_group]
         [-r] [-k Kernel] [-i Initrd] [-p Kern_Parms]
The boothost tool is responsible for generating the PXE configuration
files nodes will use to boot over the network with.  This tool can
manipulate the kernel, initrd, and kernel parameters a node group or
node will boot with.  It can optionally attempt to trigger a reinstall
of all the nodes in a node group, or a list of nodes.  The options are:
    -h             - Provide tool help (This screen)
    -v             - Print the tool version
    -l {nodename}  - Output the booting status of the given node.
                     If no name is provided list all nodes that PXE.
    -t node_group  - Update all the PXE files for all nodes in the
                     node group node_group.
    -n node_list   - Update all the PXE files for all nodes in the
                     comma seperated list of nodes.
    -s node_group  - Update all the PXE files for all nodes in the
                     node group node_group that are out of sync.
                     (This option may be removed)
    -r             - If specified attempt to connect to all affected
                     nodes and trigger a reinstall.  Uses pdsh.
    -k Kernel      - If specified it will use the kernel provided
                     in the PXE file(s) for the nodes or node_group.
                     The database will be updated accordingly.
    -i Initrd      - If specified it will use the Initrd provided
                     in the PXE file(s) for the nodes or node_group.
                     The database will be updated accordingly.
    -p Kern_Parms  - If specified it will use the kernel parameters
                     provided in the PXE file(s) for the nodes or
                     node_group.  The database will be updated
                     accordingly. ERROR:  No such host: %s
 ERROR:  No such nodegroup: %s
 Attempting to reboot:  ERROR:  Only root can reboot nodes.  Not attempting reboot! ERROR:  Unable to query database for nodegroup %s information.
 ERROR:  Unable to update node group %s database entries.
 buildimage [-h|-v| -n node_group {-i image_name}]

The buildimage tool will build the root filesystem for diskless and disked
nodes.  It uses the data in the database for a node group to determine which
packages to install.  It then creates a chroot'ed filesystem under which it
copies the files.  It then runs any post installation scripts and any user
provided custom scripts.  The arguments have the following meanings:
  -h             - Provide help on this tool.
  -v             - Print the tool version.
  -n node-group  - The name pf the node group to generate the root
                   filesystem for.
  -i image_name  - (Optional) The name to assign the generated image.
The full list of arguments is as follows: buildimage [-h|-v| -n node_group {-i image_name} {-t type}]

The buildinitrd tool creates the initial RAM disk for
 Diskless and Disked nodes running from an image. This plugin generates the Apache configuration file.
USE:  dbreport apache_conf
The resulting file should be placed in /etc/httpd/conf.d This plugin provides debugging information for support.
Currently it provides a dump of the database. This plugin generates the DHCP daemon configuration file.
No arguments are needed for the plugin. dbreport [-h|-v| -d database -u user -p password ] plugin plugin_args

The dbreport tool will run various plugins to generate configuration
files for various applications.  It may also be used to gather
information about the cluster.  See below for a list of plugins.

When run with no arguments it will generate a list of all available
plugins.  The following arguments are supported by the tool:
  -h           - Provide help on this tool.  If a plugin is specified
                 then the help for that tool will be displayed
  -v           - Print the tool version.
  -d database  - (optional) name of the database to connect to.
                 Defaults to ocsdb.
  -u user      - (optional) user of to connect to the database as.
                 Defaults to guest.
  -p password  - (optional) The password to use in connecting to the
                 database.  Defaults to guest.

Available plugins include: This plugin generates the contents of the /etc/hosts file. This plugin generates the named.conf.
USE:  dbreport named [master|slave]   (defaults to master)
No output will be generated if InstallerServeDNS=False
in the appglobals database table. This plugin generates a list of all nodes installed by the installer.
If the plugin is provided with a node group name it will generate
a list of nodes in node group. This plugin generates the DNS zone file.
USE:  dbreport reverse {network}
No output will be generated if InstallerServeDNS=False
in the appglobals database table.  The network is one of the
networks defined in the networks table in the database. This plugin generates the DNS zone file.
USE:  dbreport zone
No output will be generated if InstallerServeDNS=False
in the appglobals database table. ERROR:  Cannot determine DNS forwarders from the database!
 ERROR:  Cannot determine DNS Zone from the database!
 ERROR:  Database query failed!  Unable to determine the primary installer.
 ERROR:  Cannot find plugin: %s
 ERROR:  The database, user, and password must all be specified
 Are you sure you want to quit? Exit add hosts? Select the node group to use for the installation of new nodes. kitops: Exactly one kit operation expected. Choose from add,remmove,upgrade,list
 KUSU kitops - kit operations tool add the specified kit list all the kits available on the system specify the media iso or mountpoint for the kit remove the specified kit upgrade the specified kit ERROR: Missing hostname or IP
 Repoman help goes here Select Node Group 