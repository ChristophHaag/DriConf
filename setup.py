from distutils.core import setup

setup(name="driconf",
      version="0.0.10",
      description="DRI Configuration GUI",
      author="Felix Kuehling",
      author_email="fxkuehl@gmx.de",
      url="http://fxk.de.vu/projects_cur_en",
      py_modules=["dri", "driconf", "driconf_xpm"],
      scripts=["driconf"])

errors = 0
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
