import Ice
from springpython.context import ApplicationContextAware
from springpython.context import ObjectPostProcessor


class IKusuServant:
    pass

class KusuServerAdapterProxy(ObjectPostProcessor, ApplicationContextAware):
    """
    This container represents the ICE Adapter to be used by other appplication objects
    """
    _protocol = "ssl" #default to ssl protocol
    _port = "10000" #default port
    _ADAPTER_NAME = "KusuServerAdapterProxy"
    adapter = None
    iceObj = None
    
    def __init__(self, properties):
        print "DEBUG: Initializing AdapterProxy"
        id = Ice.InitializationData()
        id.properties = properties
        self.iceObj = Ice.initialize(id) #returns a CommunicatorI object
        self.adapter = self.iceObj.createObjectAdapterWithEndpoints(self._ADAPTER_NAME, "%s -p %s" % (self._protocol, self._port)) 
        
        
    def post_process_after_initialization(self, obj, obj_name):

        if isinstance(obj, IKusuServant):
            #register servants!
            proxy = self.app_context.get_object("kusuServerAdapterProxy")
            iceObj = proxy.iceObj
            adapter = proxy.adapter 
            adapter.add(obj, iceObj.stringToIdentity(obj.SERVANT_NAME))
            adapter.activate()
            print "DEBUG: Registering :- " + obj.SERVANT_NAME
            
            
