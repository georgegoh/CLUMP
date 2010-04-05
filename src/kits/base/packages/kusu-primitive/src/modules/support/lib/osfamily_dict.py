# The os-family dict is a python dictionary which catalogs families of operating systems.
# OS families are strings which refer to a list of OS names.

osfamily_dict = {
    'rhelfamily': ['rhel', 'centos', 'scientificlinux']
    }

if __name__ == '__main__':
    for os_map in osfamily_dict.keys():
        print os_map
