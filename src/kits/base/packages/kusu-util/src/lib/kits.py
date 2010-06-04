from path import path
from kusu.util.errors import KitinfoSyntaxError, KitPackageError
from kusu.util.rpmtool import compareEVR, RPM
from primitive.support.osfamily import getOSNames, matchTuple

try:
    import subprocess
except:
    from popen5 import subprocess

SUPPORTED_KIT_APIS = ['0.2', '0.3', '0.4']

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
    if -1 == compareVersion((kit['api'], '0'), ('0.2', '0')):
        return []

    return matchComponentsToOS(components, os)

def matchComponentsToOS(components, os):
    """
    This method returns a list of component names compatible with the operating
    system described by os.

    components: a list of components as described in the kit's kitinfo file
    os: a tuple of the form (name, major, minor, arch) describing the os to match
    """

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

def get_kit_RPM(dir):
    """
    Returns an rpmtool.RPM() object for the kit RPM in dir.
    """

    # There is (should) be only one kit RPM...
    kit_rpm_list = path(dir).files('kit-*.rpm')

    if 0 == len(kit_rpm_list):
        raise KitPackageError, 'No kit RPM found in %(dir)s' % {'dir': dir}

    # ...so we grab the first one.
    kit_rpm = kit_rpm_list[0]
    return RPM(str(kit_rpm))

def compareVersion((verA, relA), (verB, relB)):
    """Compares A and B to determine which is newer.

    returns  1 if A is newer than B,
             0 if A is the same as B, and
            -1 if B is newer than A.
    """

    return compareEVR(("0", verA, relA), ("0", verB, relB))

def run_scripts(kit_root, mode, script_arg):
    script_root = path(kit_root) / 'scripts'

    # There are no scripts to run.
    if not script_root.isdir(): return 0

    scripts = []
    for script in script_root.walkfiles('*%sscript*' % mode):
        if script.ext not in ['.pyc', '.pyo']:
            scripts.append(script)

    scripts.sort()
    for script in scripts:
        cmd = [script, script_arg]
        scriptP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = scriptP.communicate()

        if 0 != scriptP.returncode:
            return scriptP.returncode

    # All scripts succeeded.
    return 0

def generate_script_arg(operation, update_action):
    """
    Generates the argument passed to an install/uninstall script.

    operation: a string indicating the current operation, one of 'add' or
    'delete'
    update_action: boolean indicating whether this action is part of an update

    returns: the string argument to be passed to the install/uninstall script

    NOTE: this method raises a ValueError if operation is not one of 'add' or
    'delete'

    The kit install/uninstall scripts are passed one integer argument depending
    on the operation being performed. The argument represents the number of
    kits by this name which will be installed in the system after this
    operation completes.

    When a new kit is added, the add kit operation is executed, its scripts are
    passed '1' as the argument, since after the add operation is completed, one
    instance of the kit is installed in the system. When the kit is removed,
    its scripts are passed '0', since after the delete operation completes, no
    instances of the kit are installed.

    An upgrade is a combination of two steps, first an add of the new version,
    followed by a delete of the older version. In this case, the scripts of the
    newer version of the kit are passed '2' as the argument, since when the add
    operation completes, two instances of the kit are installed in the system.
    During the delete operation, the scripts of the older version of the kit
    are passed '1' as the argument, since when the delete operation completes,
    one instance of the kit will still remain (the new version) in the system.

    The table below shows this relationship:

       install script | add/remove | update
      ----------------+------------+--------
             pre/post |          1 |      2
         preun/postun |          0 |      1

    Also see http://www.ibm.com/developerworks/library/l-rpm3.html for details.
    """

    if 'add' == operation:
        if update_action:
            return '2'
        return '1'
    elif 'delete' == operation:
        if update_action:
            return '1'
        return '0'

    raise ValueError, "Unknown operation: '%s', only 'add' and 'delete' supported." % operation
