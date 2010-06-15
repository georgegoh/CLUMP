import os 
import sys
#import modules.support.log #
import logging

import primitive.support.log


class CommandFailException(Exception):
    ''' Basic Command Failure class '''
    # needs to be refactored g
    pass

class Command(object):
    #Class varibles - keep these to a minimum
    DEFAULT_LOCKDIR='/var/lock/subsys/primitive'
    def __init__(self,**kwargs):
        ''' the parent initialisation function. All command classes
        are expected to call this. Required args are the program name.
        Optionally whether the command is locked or if its logged.
        Mandatory keywords - name
        Optional keywords locked , lockdir logged, logdir '''
        #mandatory arguments
        try:
            self.name = kwargs['name']
        except:
            raise CommandFailException, 'Required keys not supplied'
        #optional arguments
        self.logged = True
        self.locked = False

        if 'locked' in kwargs:
            self.locked = kwargs['locked']
        if 'logged' in kwargs:
            self.logged = kwargs['logged']

        #initialise pre and post exec callbacks
        self.pre_execs = {}
        self.post_execs = {}

        #Initialise Locking
        if self.locked:
            try:
                self.lockdir = kwargs['lockdir']
                if not self.lockdir.endswith('/'):
                    self.lockdir = ''.join([self.lockdir,'/'])
            except:
                self.lockdir = os.getenv('PRIMITIVE_LOCKDIR', Command.DEFAULT_LOCKDIR)
            try:
                if not os.path.exists(self.lockdir):
                    os.makedirs(self.lockdir) #511 default perm
                else:
                    if not os.path.isdir(self.lockdir):
                        raise CommandFailException,\
                            'Lockdir %s is not a directory!' % self.lockdir
            except OSError,e:
                raise CommandFailException,'Failed creating lockdir: %s' % e

            self.lockfile = ''.join([self.lockdir, self.name, '.lock'])
            self.addLockingCallbacks()
        #Initialise Logging
        
        if self.logged:
            try:
                lf = []
                lf.append(kwargs['logdir'])
                if not lf[0].endswith('/'):
                    lf.append('/')
                lf.append('primitive.log')
                self.logfile = ''.join(lf)
            except KeyError:
                # Let logger.py handle the defaults.
                self.logfile = ''

            #initialise basic logging
            #additional logging callbacks can be configured similarly
            # we want to ideally offload all of this to log.py
            # once infra is up
            self.logFileHandler = None
            self.addLoggingCallbacks()


# The ranking algorithm for the callbacks is as follows:
# The callbacks are stored in a dictionary indexed by the rank.
# Within each rank, the functions are stored in an unspecified order.
# When the callbacks are run, they are run in *descending* order, 
# Highest rank first. 99 to 0. Default rank is 0.
    def __registerCallback(self,callbacks,fn,rank=0):
        ''' Register a callback into a callback dictionary,
        with a default rank of 0'''
        try:
            long(rank)
        except ValueError:
            raise CommandFailException,\
                "Invalid rank supplied for the callback"
        if not callable(fn):
            raise CommandFailException,\
                "Function supplied as a callback is not callable!"
        if rank not in callbacks.keys():
            callbacks[rank] = [fn]
        else:
            callbacks[rank].append(fn)

    def registerPostCallback(self,post,rank=0):
        '''register a callback to run after execution of business logic
        with optional rank'''
        self.__registerCallback(self.post_execs,post,rank)

    def registerPreCallback(self,pre,rank=0):
        '''register a callback to run before execution of business logic
        with optional rank'''
        self.__registerCallback(self.pre_execs,pre,rank)

    def registerCallbacks(self,pre,post,rank=0):
        ''' convenience function to register both pre and post callbacks with
        same rank'''
        self.registerPreCallback(pre,rank)
        self.registerPostCallback(post,rank)

    #execution framework
    def execute(self):
        ''' calls execImpl() after running pre and post exec callbacks '''
        # sort the pre exec callbacks in a descending order
        # execute each function in that rank
        try:
            for rank in sorted(self.pre_execs.keys(), lambda x,y: y - x):
                [fn() for fn in self.pre_execs[rank]]
            retval =  self.execImpl()
        # ensure post_execs are executed no matter what happens in execImpl.
        finally:
            for rank in sorted(self.post_execs.keys(), lambda x,y: y - x):
                [fn() for fn in self.post_execs[rank]]
        return retval 

    def execImpl(self):
        raise NotImplementedError

    #locking related functions.
    def __touch(self):
        f = open(self.lockfile,'w')
        f.close()

    def lock(self):
        ''' unconditionally create a lock file'''
        self.__touch()

    def unlock(self):
        ''' unconditionally remove a lock file'''
        if self.isLocked():
            os.remove(self.lockfile)

    def isLocked(self):
        ''' predicate to check if a lock associated with the command exists'''
        if os.path.exists(self.lockfile):
            return True
        else:
            return False

    def tryLock(self):
        ''' try to obtain a lock, fail if already locked or if lock cannot
        be obtained'''
        if self.isLocked():
            raise CommandFailException,\
                "This command cannot run as there is already another running\
 instance of the command."
        #potential race here
        else:
            try:
                self.lock()
            except IOError:
                raise CommandFailException,"Failed to lock %s"%self.lockfile

    def tryUnlock(self):
        '''Try to unlock the lock, fail if no lock present or
        unable to unlock'''
        if not self.isLocked():
            raise CommandFailException,"There is no lock file to unlock!"
        else:
            try:
                self.unlock()
            except:
                raise CommandFailException,"Failed to unlock %s"% self.lockfile

    def addLockingCallbacks(self):
        ''' Convenience function to add locking callbacks'''
        self.registerCallbacks(self.tryLock,self.tryUnlock)

    #logging functions
    def enableLogging(self):
        ''' This functions enables logging and initialises returns a Logger ( see pydoc logging.Logger)
        for logging. '''
        primitive.support.log.setLoggerClass()
        self.logger = primitive.support.log.getPrimitiveLog(self.name)
        self.logFileHandler = self.logger.addFileHandler(self.logfile) # this can also be managed in execImpl for custom handlers
        self.logger.info('Begin Logging session')

    def disableLogging(self): 
        ''' self.logger can no longer be used after a call to this function '''
        self.logger.info('End Logging session')
        if self.logFileHandler:
            self.logFileHandler.close()
            self.logger.removeHandler(self.logFileHandler)
        #close logger


    def addLoggingCallbacks(self):
        ''' Adds logging support'''
        self.registerCallbacks(self.enableLogging,self.disableLogging)

