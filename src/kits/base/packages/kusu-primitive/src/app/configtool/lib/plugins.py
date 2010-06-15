from primitive.core.command import CommandFailException
from path import path
import Cheetah.Template

class PluginException(CommandFailException):
    ''' This class is always called in the context of a command and thus needs
    to inherit it'''
    pass

class BasePlugin(object):
    def __init__(self,template,args_dict):
        self.validateArgs(args_dict)
        self.validateTemplate(template)
        self.args_dict = args_dict
        self.template = template
    def run(self):
        try:
            output = Cheetah.Template.Template(file=str(self.template),\
                                                   searchList = [self.args_dict])
        except Exception,e:
            raise PluginException,"Failed to parse template! %s" % e 
        
        return str(output)

    def validateArgs(self,args_dict):
        '''This function must be overridden by a plugin, and should mostly be enough'''
        raise NotImplementedError

    def validateTemplate(self,template):
        '''This function is called, but is most likely not used. It can be used if a plugin needs it'''
        pass
