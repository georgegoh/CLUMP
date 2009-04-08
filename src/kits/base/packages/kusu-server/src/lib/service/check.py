import IPy
from kusu.boot.distro import DistroFactory
from kusu.service.exceptions import ExceptionInfo
from primitive.system.software import probe
from primitive.system.hardware import net

class Checker(object):
    """ Abstract class for describing classes which can
        get failures(e.g., from checking system devices).
    """
    def getFailures(cls, *args, **kwargs):
        """ Used to get failures."""
        return cls().getFailuresImpl(*args, **kwargs)
    getFailures = classmethod(getFailures)

    def getFailuresImpl(self, *args, **kwargs):
        """ Actual implementation by child classes."""
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
                                  msg='Cannot detect OS of media')]
        elif media.ostype.lower() != os.lower() or \
             media.version != ver or \
             media.arch != arch:
            return [ExceptionInfo(title='Media/OS mismatch',
                           msg='Media(%s,%s,%s) does not match system OS(%s, %s, %s)' % 
                           (media.ostype, media.version, media.arch, os, ver, arch))]
        return []


class Provision(Checker):
    def getFailuresImpl(self, *args, **kwargs):
        provision = kwargs.get('provision', None) or args[0]

        intfs_dict = net.getPhysicalInterfaces()
        if provision['device'] not in intfs_dict:
            return [ExceptionInfo(title='Provision interface missing',
                            msg='Provision interface %s specified does not exist' %
                            provision['device'])]
        
        try:
            IPy.IP(provision['ip']).make_net(provision['netmask'])
        except Exception, e:
            return [ExceptionInfo(title='Provision IP/Netmask Error',
                                  msg=str(e))]
        return []


class Disk(Checker):
    def getFailuresImpl(self, *args, **kwargs):
        # Disk requirements
        return []
