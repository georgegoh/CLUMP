from path import path
from kusu.util.errors import KitinfoSyntaxError

def processKitInfo(kitinfo):
    """ Loads the kitinfo file and returns a tuple containing two elements - the kit metainfo
        and a list of component metainfo contained in that file. A metainfo is a dict object.
    """
    kitinfo = path(kitinfo)
    if not kitinfo.isfile(): return ({},[])

    ns = {}

    # If there is a syntax error in the kitinfo file, holla!
    try:
        execfile(kitinfo,ns)
    except SyntaxError, e:
        error_message = "%s in kitinfo file %s at line %s, column %s" % \
                        (e.msg, e.filename, e.lineno, e.offset)
        raise KitinfoSyntaxError, error_message

    kit = ns.get('kit',{})
    components = ns.get('components',[])

    return (kit,components)
