from distutils.core import setup

setup(name="driconf",
      version="0.2.5",
      description="A configuration GUI for DRI drivers",
      author="Felix Kuehling",
      author_email="fxkuehl@gmx.de",
      url="http://dri.freedesktop.org/wiki/DriConf",
      py_modules=["dri", "driconf"],
      scripts=["driconf"],
      data_files=[("share/driconf", ["card.png", "screen.png", "screencard.png",
                                     "drilogo.jpg"]),
                  ("share/locale/de/LC_MESSAGES", ["de/LC_MESSAGES/driconf.mo"])
                  ])

#
# Search for obsolete files.
#
from os.path import isfile, isdir, join
from distutils.sysconfig import get_python_lib
obsoleteFiles = []
for prefix in [None, "/usr/local"]:
    if not prefix:
        pyLibPath = get_python_lib()
    else:
        pyLibPath = get_python_lib(prefix=prefix)
    if not isdir (pyLibPath):
        continue
    for f in ["driconf_xpm.py", "driconf_xpm.pyc", "driconf_xpm.pyo"]:
        path = join (pyLibPath, f)
        if isfile (path):
            obsoleteFiles.append (path)
if obsoleteFiles:
    print "\n*** Obsolete files from previous DRIconf versions were found on " \
          "your system.\n*** You can probably delete them:"
    for f in obsoleteFiles:
        print "***\t%s" % f

#
# Check if required packages are installed
#
errors = 0
try:
    import pygtk
    pygtk.require ("2.0")
    import gtk
except:
    print "\n*** Warning: importing gtk version 2.0 doesn't work."
    errors = 1
try:
    import xml.parsers.expat
except:
    if not errors:
        print
    print "*** Warning: importing xml.parsers.expat doesn't work."
    errors = 1

if errors:
    print "*** Warning: driconf will probably not work for the above reason(s)."
