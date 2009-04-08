
import Demo, Ice
from kusu2.server.adapter import IKusuServant

from springpython.context import ApplicationContextAware
from springpython.context import ObjectPostProcessor

class PrinterI(Demo.Printer , IKusuServant):
    """
        Dummy Class to test dependency injection via SpringPython
    """
    SERVANT_NAME = "SimplePrinter"
    networkSvc = None
    
    def printString(self, s, current=None):
    
        print s
        
    def getInterfaces(self, s):
        return self.networkSvc.listInterfaces()
        
    