from distutils.core import setup

setup(name="driconf",
      version="0.1.2",
      description="DRI Configuration GUI (gtk-1.2)",
      author="Felix Kuehling",
      author_email="fxkuehl@gmx.de",
      url="http://dri.sourceforge.net/cgi-bin/moin.cgi/DriConf",
      py_modules=["dri", "driconf", "driconf_xpm"],
      scripts=["driconf"])

errors = 0
try:
    import pygtk
    # make sure gtk version 1.2 is used.
    pygtk.require ("1.2")
except ImportError:
    # not supported everywhere, so ignore import errors
    pass
try:
    import gtk
except ImportError:
    print "Warning: importing gtk doesn't work."
    errors = 1
try:
    import xml.parsers.expat
except ImportError:
    print "Warning: importing xml.parsers.expat doesn't work."
    errors = 1

if errors:
    print "Warning: driconf will probably not work for the above reason(s)."
