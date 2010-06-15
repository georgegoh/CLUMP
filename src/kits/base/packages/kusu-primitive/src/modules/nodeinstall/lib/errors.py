from  primitive.core.errors import ModuleException

class NIISourceUnavailableError(ModuleException): pass
class EmptyNIISource(ModuleException): pass
class ParseNIISourceError(ModuleException): pass

class InvalidPartitionSchema(ModuleException):pass
