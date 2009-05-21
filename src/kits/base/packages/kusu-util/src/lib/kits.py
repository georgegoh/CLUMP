from path import path
from kusu.util.errors import KitinfoSyntaxError
from primitive.support.osfamily import getOSNames, matchTuple

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

def getKitComponentsMatchingOS(kitinfo, os):
    """
    This method returns a list of component names compatible with the operating
    system described by os as stated in the specified kitinfo file.

    kitinfo: a string containing the path to the authoritative kitinfo file
    os: a tuple of the form (name, major, minor, arch) describing the os to match
    """

    kitinfo = path(kitinfo)
    if not kitinfo.isfile(): return []

    kit, components = processKitInfo(kitinfo)
    if kit['api'] != '0.2':
        return []

    target_os = (os.name, os.major, os.minor, os.arch)
    components_list = []

    for comp in components:
        os_tuples = []

        try:
            for os_tuple in comp['os']:
                for os_name in getOSNames(os_tuple['name'], default=[os_tuple['name']]):
                    os_tuples.append((os_name, os_tuple['major'], os_tuple['minor'], os_tuple['arch']))
        except KeyError:
            break

        try:
            if matchTuple(target_os, os_tuples):
                components_list.append(comp['pkgname'])
        except KeyError:
            pass

    return components_list
