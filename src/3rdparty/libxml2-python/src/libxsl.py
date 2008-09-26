#
# Both libxml2mod and libxsltmod have a dependancy on libxml2.so
# and they should share the same module, try to convince the python
# loader to work in that mode if feasible
#
import sys
if not hasattr(sys,'getdlopenflags'):
    import libxml2mod
    import libxsltmod
    import libxml2
else:
    try:
        from dl import RTLD_GLOBAL, RTLD_NOW
    except ImportError:
        RTLD_GLOBAL = -1
        RTLD_NOW = -1
        try:
            import os
            osname = os.uname()[0]
            if osname == 'Linux' or osname == 'SunOS':
                RTLD_GLOBAL = 0x00100
                RTLD_NOW = 0x00002
            #
            # is there a better method ?
            #
#            else:
#                print "libxslt could not guess RTLD_GLOBAL and RTLD_NOW " + \
#                      "on this platform: %s" % (osname)
        except:
	     pass
#            print "libxslt could not guess RTLD_GLOBAL and RTLD_NOW " + \
#                  "on this platform: %s" % (osname)

    if RTLD_GLOBAL != -1 and RTLD_NOW != -1:
        try:
            flags = sys.getdlopenflags() 
            sys.setdlopenflags(RTLD_GLOBAL | RTLD_NOW)
            try:
                import libxml2mod
                import libxsltmod
                import libxml2
            finally:
                sys.setdlopenflags(flags)
        except:
            import libxml2mod
            import libxsltmod
            import libxml2
    else:
        import libxml2mod
        import libxsltmod
        import libxml2

class extensionModule:
    def _styleInit(self, style, URI):
        return self.styleInit(stylesheet(_obj=style), URI)

    def _styleShutdown(self, style, URI, data):
        return self.styleShutdown(stylesheet(_obj=style), URI, data)

    def _ctxtInit(self, ctxt, URI):
        return self.ctxtInit(transformCtxt(_obj=ctxt), URI)

    def _ctxtShutdown(self, ctxt, URI, data):
        return self.ctxtShutdown(transformCtxt(_obj=ctxt), URI, data)

    def styleInit(self, style, URI):
        """Callback function when used in a newly compiled stylesheet,
	   the return value is passed in subsequent calls"""
	pass

    def styleShutdown(self, style, URI, data):
        """Callback function when a stylesheet using it is destroyed"""
	pass

    def ctxtInit(self, ctxt, URI):
        """Callback function when used in a new transformation process,
	   the return value is passed in subsequent calls"""
	pass

    def ctxtShutdown(self, ctxt, URI, data):
        """Callback function when a transformation using it finishes"""
	pass

#
# Everything below this point is automatically generated
#

