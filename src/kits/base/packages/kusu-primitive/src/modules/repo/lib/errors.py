from primitive.core.errors import ModuleException

class RepoException(ModuleException):
    pass
class RepoCreationError(RepoException):
    pass
class RepoUpdateImgError(RepoException):
    pass
