from kusu.util.errors import KusuError

class ExceptionInfo(object):
    def __init__(self, title, msg):
        self.title = title
        self.msg = msg

# Kusu Service
class ServiceException(KusuError): 
    def __init__(self, exception_msgs):
        self.messages = exception_msgs

class ServiceInstallException(ServiceException): pass

class InstallConfMissingException(ServiceInstallException): pass
class InstallConfParseException(ServiceInstallException): pass
class InvalidConfException(ServiceInstallException): pass
class PrerequisiteCheckFailedException(ServiceInstallException): pass
