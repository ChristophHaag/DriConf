from distutils.core import setup

setup(name="driconf",
      version="0.2.0",
      description="DRI Configuration GUI",
      author="Felix Kuehling",
      author_email="fxkuehl@gmx.de",
      url="http://fxk.de.vu/projects_cur_en",
      py_modules=["dri", "driconf", "driconf_xpm"],
      scripts=["driconf"])

errors = 0
try:
    import pygtk
    pygtk.require ("2.0")
    import gtk
except:
    print "Warning: importing gtk version 2.0 doesn't work."
    errors = 1
try:
    import xml.parsers.expat
except:
    print "Warning: importing xml.parsers.expat doesn't work."
    errors = 1

if errors:
    print "Warning: driconf will probably not work for the above reason(s)."
