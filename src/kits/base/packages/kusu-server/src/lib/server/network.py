from kusu.server.adapter import IKusuServant
from kusu2.config.net import DnsConfig, INetwork, NetworkException
import kusu.ipfun as ipfun

class NetworkServant(INetwork , IKusuServant):
    """
        
    """
    SERVANT_NAME = "NetworkServant"
    networkSvc = None #Dependency-injected via Spring
    
    def getInterfaces(self, s):

        ifaceNames = self.networkSvc.getInterfaces()

        return ifaceNames
    
    def getInterfaceConfig(self, interfaceName, current=None):

        cfg = self.networkSvc.getInterfaceConfig(interfaceName)

        if cfg is None:
            raise NetworkException("Invalid Interface : [%s]" % (interfaceName))

        return cfg


    def updateInterfaceConfig(self, s, config):
        self.networkSvc.updateInterfaceConfig(config)
                    
    def getDnsConfig(self, s ):
        cfg = self.networkSvc.getDnsConfig()
        
        return cfg
                
    def updateNameserverSettings(self, s):
        """
           Currently this method does not do anything. We probably want to
           automate DNS (/etc/resolv.conf) settings by generating from
           what's been set as the cluster interface/network.
        """
        pass
        
