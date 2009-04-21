import IPy
from path import path
from kusu.boot.distro import DistroFactory
from kusu.service.exceptions import ExceptionInfo
from primitive.system.software import probe
from primitive.system.hardware import probe as hwprobe
from primitive.system.hardware import net
from primitive.support.type import Struct

class Checker(object):
    """ Abstract class for describing classes which can
        get failures(e.g., from checking system devices).
    """
    @classmethod
    def getFailures(cls, *args, **kwargs):
        """ Used to get failures."""
        return cls().getFailuresImpl(*args, **kwargs)

    def getFailuresImpl(self, *args, **kwargs):
        """ Actual implementation by child classes."""
        #return []
        raise NotImplementedError


class Media(Checker):
     def getFailuresImpl(self, *args, **kwargs):
        """ Check if media at 'loc' location matches the current(native)
            distro. If no match, then return value is a list of
            ExceptionInfo objects, else returns an empty list.
        """
        loc = kwargs.get('media_loc', None) or args[0]

        media = DistroFactory(loc)
        os, ver, arch = probe.OS()
        if not (media.ostype and media.version and media.arch):
            return [ExceptionInfo(title='Media not detected',
                                  msg='Cannot detect OS of media at %s' % loc)]
        elif media.ostype.lower() != os.lower() or \
             media.version != ver or \
             media.arch != arch:
            return [ExceptionInfo(title='Media/OS mismatch',
                           msg='Media(%s,%s,%s) at %s does not match system OS(%s, %s, %s)' % 
                           (media.ostype, media.version, media.arch, loc, os, ver, arch))]
        return []


class Provision(Checker):
    def getFailuresImpl(self, *args, **kwargs):
        provision = kwargs.get('provision', None) or args[0]

        intfs_dict = net.getPhysicalInterfaces()
        # does the requested network device actually exist?
        if provision['device'] not in intfs_dict:
            return [ExceptionInfo(title='Provision interface missing',
                            msg='Provision interface %s specified does not exist' %
                            provision['device'])]

        # does the IP/netmask make sense?
        try:
            IPy.IP(provision['ip']).make_net(provision['netmask'])
        except Exception, e:
            return [ExceptionInfo(title='Provision IP/Netmask Error',
                                  msg=str(e))]

        intf = intfs_dict[provision['device']]
        # is the interface on static or dhcp?
        if intf['dhcp']:
            return [ExceptionInfo(title='Provision interface is not static',
                        msg='Requested provision interface %s is not a static interface' %
                            (provision['device']))]

        # if interface is currently configured, does it clash with the
        # user-defined settings?
        existing_ip = intf['ip']
        existing_netmask = intf['netmask']
        intf_already_enabled = existing_ip and existing_netmask
        intf_matches_conf = (existing_ip == provision['ip'] and \
                             existing_netmask == provision['netmask'])
        if intf_already_enabled and not intf_matches_conf:
            overwrite = provision.get('overwrite_existing', False)
            if not overwrite:
                return [ExceptionInfo(title='Provision interface has conflicting configuration',
                            msg='Requested provision interface %s already has a configuration(%s/%s) which conflicts with requested configuration(%s/%s)' % 
                                (provision['device'], existing_ip, existing_netmask,
                                 provision['ip'], provision['netmask']))]
        return []


class Disk(Checker):
    usable_fstypes=set(['ext2', 'ext3', 'reiserfs'])
    required_keys=set(['kusu', 'depot', 'home'])
    min_req_MB = {'kusu': 500, 'depot': 8000}

    def getFailuresImpl(self, *args, **kwargs):
        rv = []

        # Disk requirements
        disk = kwargs.get('disk', None) or args[0]

        # do some set mathematics here to look for missing keys.
        missing_keys = self.required_keys - set(disk.keys())
        if missing_keys:
            rv.append(ExceptionInfo(title='Required paths missing',
                        msg='%s paths need to be defined in the config' %
                        list(missing_keys)))
        keys_to_check = self.required_keys.intersection(disk.keys())

        # all paths given must be absolute paths.
        failed_keys = []
        for k in keys_to_check:
            if not disk[k].startswith('/'):
                failed_keys.append(k)
        if failed_keys:
            rv.append(ExceptionInfo(title='Paths are not absolute',
                        msg='Paths defined need to be absolute%s.' % failed_keys))

        # home must already exist.
        if not path(disk['home']).exists():
            rv.append(ExceptionInfo(title='Home directory does not exist',
                        msg='Defined home directory "%s" needs to be a valid directory.' %
                        disk['home']))

        # check that all defined paths fulfill minimum free space requirements.
        mntpnt_d = self.probeMountPoints()
        # longest paths at top of the list.
        mntpnts = mntpnt_d.keys()
        mntpnts.sort(reverse=True)
        for k in keys_to_check:
            target_path = disk[k]
            for m in mntpnts:
                if target_path.startswith(m):
                    # Found longest match. Now check for min size requirements.
                    m_size_MB = long(mntpnt_d[m].available[:-1]) # trim the last 'M' unit character.
                    min_req_size_MB = self.min_req_MB.get(k, 0)
                    if m_size_MB < min_req_size_MB:
                        rv.append(ExceptionInfo(title='Insufficient available space for mountpoint',
                                    msg='%s(%s) needs %dM, %s(%s) has %s available\n' %
                                        (target_path, k, self.min_req_MB[k],
                                         m, mntpnt_d[m].dev, mntpnt_d[m].available)))
        return rv

    @classmethod
    def probeMountPoints(cls):
        # sort out the hwprobe output to our needs.
        d = hwprobe.getMountpoints()
        d = hwprobe.df()
        mntpnt_d = Struct()
        for k,v in d.iteritems():
            if v.mntpnt:
                mntpnt_d[v.mntpnt] = Struct(dev=k, fstype=v.fstype, available=v.available)
        return mntpnt_d
