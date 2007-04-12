# urlgrabber distutils setup
import re as _re
import urlgrabber as _urlgrabber

name = "urlgrabber"
description = "A high-level cross-protocol url-grabber"
long_description = _urlgrabber.__doc__
license = "LGPL"
version = _urlgrabber.__version__
_authors = _re.split(r',\s+', _urlgrabber.__author__)
author       = ', '.join([_re.sub(r'\s+<.*',        r'', _) for _ in _authors])
author_email = ', '.join([_re.sub(r'(^.*<)|(>.*$)', r'', _) for _ in _authors])
url = _urlgrabber.__url__

packages = ['urlgrabber']
package_dir = {'urlgrabber':'urlgrabber'}
scripts = ['scripts/urlgrabber']
data_files = [('share/doc/' + name + '-' + version,
               ['README','LICENSE', 'TODO', 'ChangeLog'])]
options = { 'clean' : { 'all' : 1 } }
classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Internet :: File Transfer Protocol (FTP)',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules'
      ]

# load up distutils
if __name__ == '__main__':
  config = globals().copy()
  keys = config.keys()
  for k in keys:
    #print '%-20s -> %s' % (k, config[k])
    if k.startswith('_'): del config[k]

  from distutils.core import setup
  setup(**config)
