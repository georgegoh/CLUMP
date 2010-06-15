#!/usr/bin/env python
import os
import tempfile
import logging
import tarfile
from primitive.core.command import CommandFailException
from primitive.configtool.commands import ConfigCommand
from primitive.configtool.plugins import BasePlugin
try:
    import subprocess
except:
    from popen5  import subprocess
from path import path
from nose.tools import assert_raises

tmpBaseDir = '/tmp/non_existent' #failsafe defaults

def setup():
    global tmpBaseDir
    tmpBaseDir = tempfile.mkdtemp('primitive-configtool')

    pass
def teardown():
    path(tmpBaseDir).rmtree()


def touch(filename):
    f = open(filename,'w')
    f.close()

class TestPlugin(BasePlugin):
    ''' Simple class just cascades template and arguments to cheetah'''
    def validateArgs(self,args_dict):
        pass

class TestConfigTool(object):
    '''Test Config Tool'''
    def setUp(self):
        ''' Sets up some class wide artifacts needed for each test'''
        self.conf_str = """# Test Conf file for ${ident}
var1=$var1
var2=$var2
#if $varExists('var3')
var3=$var3
#end if
var4=$var4
#for $v in $var5
Testloop $v
#end for
"""
        self.test_out1 ="""# Test Conf file for TEST1
var1=V1
var2=V2
var3=V3
var4=V4
Testloop V5
"""
        self.test_out2="""# Test Conf file for TEST2
var1=V1
var2=V2
var4=V4
"""
        self.test_out3="""# Test Conf file for TEST3
var1=V1
var2=V2
var3=V3
var4=V4
Testloop V5a
Testloop V5b
Testloop V5c
Testloop V5d
Testloop V5e
"""
        self.test_conf = path(tmpBaseDir) / 'cheetah_test.tmpl'
        f = open(self.test_conf,'w')
        f.write(self.conf_str)
        f.close()
    def tearDown(self):
        pass

    def testConfig0(self):
        '''ConfigTool:Test0:Negative test cases for plugin parsing'''
        tmpl = ''.join(['file://', self.test_conf])
        assert_raises(NotImplementedError,
                      ConfigCommand,name='TestConfig0',logged=False,
                      locked=False,
                      plugin=BasePlugin,template=tmpl,
                      plugin_args={})  
        #Base Plugin must be subclassed
        #Must provide valid plugin
        assert_raises(CommandFailException,
                      ConfigCommand,
                      name='TestConfig0',logged=False,locked=False,
                      plugin='IcauseFailure',template=tmpl,
                      plugin_args= {})
        
    def testConfig1(self):
        ''' ConfigTool:Test1:Test if all variables are parsed correctly.'''
        #Test that config tool cannot be locked
        # Comment this test until cascading commands can be properly handled
#         assert_raises(CommandFailException,
#                       ConfigCommand,
#                       name='TestConfig1',logged=False,locked=True,
#                       plugin=TestPlugin,
#                       template=''.join(['file://', self.test_conf]),
#                       plugin_args= {})
        # Perform a positive test to ensure everything works for the
        # Default case
        args = {'ident' : 'TEST1',
                'var1' : 'V1',
                 'var2' : 'V2',
                 'var3' : 'V3',
                 'var4' : 'V4',
                 'var5' : ['V5'] # This needs to be a list 
                 }
        inputs = { 'name' : 'TEST1',
                   'template'  : ''.join(['file://', self.test_conf]),
                   'plugin' : TestPlugin,
                   'plugin_args' : args }
                 
        t = ConfigCommand(**inputs)
        output_str = t.execute()
        print output_str
#        print self.test_out1
        assert output_str == self.test_out1
    def testConfig2(self):
        ''' ConfigTool:Test2:Test if statement parsing'''
        # Test IF condition and sending a blank list for loop
        args = {'ident' : 'TEST2',
                'var1' : 'V1',
                 'var2' : 'V2',
                 'var4' : 'V4',
                 'var5' : [] # Send in an empty list
                 }
        inputs = { 'name' : 'TEST2',
                   'template'  : ''.join(['file://', self.test_conf]),
                   'plugin' : TestPlugin,
                   'plugin_args' : args }
                 
        t = ConfigCommand(**inputs)
        output_str = t.execute()
        print output_str
#        print self.test_out1
        assert output_str == self.test_out2
    def testConfig3(self):
        ''' ConfigTool:Test3:Test for statement parsing'''
        # Test loop iteration
        args = {'ident' : 'TEST3',
                'var1' : 'V1',
                 'var2' : 'V2',
                'var3' : 'V3',
                 'var4' : 'V4',
                 'var5' : ['V5a','V5b','V5c','V5d','V5e'] 
                 }
        inputs = { 'name' : 'TEST3',
                   'template'  : ''.join(['file://', self.test_conf]),
                   'plugin' : TestPlugin,
                   'plugin_args' : args }
                 
        t = ConfigCommand(**inputs)
        output_str = t.execute()
        print output_str
#        print self.test_out1
        assert output_str == self.test_out3
    
