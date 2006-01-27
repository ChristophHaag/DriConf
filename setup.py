from distutils.core import setup

langs = ["de", "es", "it", "ru"]
translations = []
for lang in langs:
    translations.append (("share/locale/%s/LC_MESSAGES" % lang,
                          ["%s/LC_MESSAGES/driconf.mo" % lang]))

setup(name="driconf",
      version="0.9.0",
      description="A configuration applet for DRI drivers",
      author="Felix Kuehling",
      author_email="fxkuehl@gmx.de",
      url="http://dri.freedesktop.org/wiki/DriConf",
      py_modules=["dri", "driconf", "driconf_commonui", "driconf_complexui",
                  "driconf_simpleui"],
      scripts=["driconf"],
      data_files=[("share/driconf", ["card.png", "screen.png", "screencard.png",
                                     "drilogo.jpg"])] + translations)

#
# Search for obsolete files.
#
# driconf_xpm is gone for good, the other two python modules were moved to
# <prefix>/lib/driconf/...
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
    for f in ["driconf_xpm.py", "driconf_xpm.pyc", "driconf_xpm.pyo",
              "driconf.py", "driconf.pyc", "driconf.pyo",
              "dri.py", "dri.pyc", "dri.pyo"]:
        path = join (pyLibPath, f)
        if isfile (path):
            obsoleteFiles.append (path)
if obsoleteFiles:
    print "\n*** Obsolete files from previous DRIconf versions were found on " \
          "your system.\n*** Unless you tweaked setup.cfg you can probably " \
          "delete them:"
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
    print "\n*** Warning: importing GTK version 2 doesn't work."
    errors = 1
else:
    if gtk.check_version(2, 4, 0):
        print "\n*** Warning: DRIconf requires GTK 2.4 or newer."
        errors = 1
try:
    import xml.parsers.expat
except:
    if not errors:
        print
    print "*** Warning: importing xml.parsers.expat doesn't work."
    errors = 1

if errors:
    print "*** Warning: DRIconf will probably not work for the above reason(s)."
