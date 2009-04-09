import atexit
from path import path
from tempfile import mkstemp
from kusu.server.adapter import IKusuServant
from kusu.service.exceptions import ServiceInstallException
from kusu.service.exceptions import ExceptionInfo as ServiceExceptionInfo
from kusu.remote import ISetup, InstallException, ExceptionInfo
import kusu.ipfun as ipfun

def cleanup(file_handle):
    """ Housekeeping"""
    if isinstance(file_handle, file):
        file_handle.close()
        f = file_handle.name
        if not isinstance(f, path):
            f = path(f)
        if f.exists():
            f.remove()
    elif isinstance(file_handle, path):
        file_handle.remove()
    else:
        f = path(file_handle)
        if f.exists():
            f.remove()


class InstallServant(ISetup, IKusuServant):
    """
        
    """
    SERVANT_NAME = "InstallServant"
    installSvc = None #Dependency-injected via Spring
    cleanFiles = True
    
    def install(self, conf, current=None):
        config_fh = self._getConfigFileHandle()
        config_fh.write(conf)
        config_fh.close()
        try:
            self.installSvc.install(config_fh.name)
        except ServiceInstallException, e:
            seq = []
            for info in e.messages:
                if isinstance(info, ServiceExceptionInfo):
                    ei = ExceptionInfo(title=info.title, msg=info.msg)
                    seq.append(ei)
            raise InstallException(messages=tuple(seq))

    def _getConfigFileHandle(self):
        # Final implementation should write this file
        # to a proper place like /opt/kusu/var/cache/install.conf.ddmmyy
        tmpfile_path = path(mkstemp()[1])
        tmpfile = tmpfile_path.open(mode='r+w')
        if self.cleanFiles:
            atexit.register(cleanup, tmpfile)
        return tmpfile
        ##
