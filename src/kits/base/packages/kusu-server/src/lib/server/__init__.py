import Ice
Ice.loadSlice('/opt/kusu/server/conf/kusu.ice')
from springpython.config import  PythonConfig, Object
from springpython.context import ObjectPostProcessor, scope

class IcePropertySetter:
    """
        This utility class is instantiated from within applicationContext.xml and
        performs the explicit setting of the Ice config settings. 
    """       
    def __init__(self, propertiesObj, propertyDict):
        for key in propertyDict.keys():
            propertiesObj.setProperty(key, propertyDict[key])


class KusuServerApplicationContext(PythonConfig):
    """
      This config object is used to encapsulate the Ice
      createProperties() factory method. We need this to programmatically set Ice config
      options from within our applicationContext.xml file.
    """
    def __init__(self):
        print "DEBUG: __init__ for KusuServerApplicationContext"
        super(KusuServerApplicationContext, self).__init__()
              
    @Object(scope.SINGLETON)
    def IceProperties(self):
        print "Debug: calling Ice.createProperties()"
        return Ice.createProperties()
        
        
