# Python interface to DRI configuration

# Copyright (C) 2003  Felix Kuehling

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# Contact: http://fxk.de.vu/

import os
import string
import xml.parsers.expat

class Error (Exception):
    """ Base class for DRIError and XMLError """
    def __init__ (self, problem):
        self.problem = problem
    def __str__ (self):
        return self.problem

class DRIError (Error):
    """ Errors interfacing with xdriinfo """
    pass

class XMLError (Error):
    """ Errors in the DRI configuration data """
    pass

def XDriInfo (argStr, dpy = None):
    """ Call xdriinfo and raise DRIError on different failure conditions """
    if dpy != None:
        dpyStr = "-display " + dpy + " "
    else:
        dpyStr = ""
    infopipe = os.popen ("xdriinfo " + dpyStr + argStr, "r")
    driInfo = infopipe.read ()
    result = infopipe.close ()
    if result != None:
        signal = result & 0xff
        status = result >> 8
        if signal != 0:
            raise DRIError ("xdriinfo killed by signal " + signal)
        elif status == 127:
            raise DRIError ("xdriinfo not found")
        else:
            raise DRIError ("xdrinfo failed")
    return driInfo

def StrToValue (str, type):
    """ Helper: convert str to given type.

    Raises an XMLError if str is not of the correct type. """
    try:
        if type == "int" or type == "enum":
            return int (str);
        elif type == "float":
            return float (str);
        else:
            if str == "true":
                return 1
            elif str == "false":
                return 0
            else:
                raise ValueError
    except ValueError:
        raise XMLError ("invalid value '" + str + "' for type '" + type + "'")

def ValueToStr (value, type):
    """ Helper: convert value of given type to string. """
    if type == "int" or type == "enum" or type == "float":
        return str(value)
    elif value:
        return "true"
    else:
        return "false"

def GetDesc (desc, preferredLangs):
    """ Helper: get a description with a list of language preferences.

    If the specified languages are not available then try english.
    If that doesn't work either, return any description. """
    for lang in preferredLangs:
        if desc.has_key (lang):
            return desc[lang]
    if desc.has_key ("en"):
        return desc["en"]
    if len(desc.values()) > 0:
        return desc.values()[0]
    return ""

class Range:
    """ An interval """
    def __init__ (self, str, type):
        """ Parse str as a range.

        Raises an XMLError if str is not a legal range. """
        assert type == "int" or type == "enum" or type == "float"
        list = string.split (str, ":")
        if len (list) == 0 or len (list) > 2:
            raise XMLError ("Invalid range '" + str + "'")
        if len (list) >= 1:
            self.start = StrToValue (list[0], type)
        if len (list) == 2:
            self.end = StrToValue (list[1], type)
        else:
            self.end = self.start

    def __str__ (self):
        if self.start == self.end:
            return str(self.start)
        else:
            return str(self.start) + ":" + str(self.end)

class OptDesc:
    """ An option description in one language with enum values. """
    def __init__ (self, lang, text):
        self.lang = lang
        self.text = text
        self.enums = {}

    def __str__ (self):
        result = '<description lang="' + self.lang + '" text="' + self.text + \
                 '">\n'
        for value in sort(self.enums.keys()):
            result = result + '<enum value="' + str(value) + '" text="' + \
                     self.enums[value] + '" />\n'
        result = result + '</description>'
        return result

class OptInfo:
    """ All advertised information about an option. """
    def __init__ (self, name, type, default, valid = None):
        """ Initialize option information.

        Raises XMLError if
          - type is illegal
          - default is not a valid value of type
          - valid attribute is specified for a bool option
          - valid is specified but illegal """
        self.name = name

        if type != "int" and type != "enum" and type != "float" \
               and type != "bool":
            raise XMLError ("invalid type '" + type + "'")
        self.type = type
        self.valid = None
        if valid:
            if type == "bool":
                raise XMLError (
                    "valid attribute is not allowed with bool options")
            else:
                self.valid = [Range(x, type)
                              for x in string.split (valid, ",")]
        if not self.validate (default):
            raise XMLError ("default value is out of valid range")
        else:
            self.default = StrToValue (default, type)
        self.desc = {}

    def __str__ (self):
        result = '<option name="' + self.name + '" type="' + self.type + \
                 '" default="' + ValueToStr(self.default, self.type) + '" '
        if self.valid:
            return result + 'valid="' + \
                   reduce(lambda x,y: x+','+y, map(str,self.valid)) + \
                   '" />'
        else:
            return result + '/>'

    def validate (self, str):
        """ Check that str is of correct type and in a valid range. """
        try:
            v = StrToValue (str, self.type)
        except XMLError:
            return 0
        if self.valid:
            for r in self.valid:
                if v >= r.start and v <= r.end:
                    return 1
            return 0
        else:
            return 1

    def getDesc (self, preferredLangs):
        return GetDesc (self.desc, preferredLangs)

class OptSection:
    """ Representation of an option section.

    Contains descriptions and OptInfos as dictionaries. Options are also
    in a list so they can be extracted in a meaningful order. """
    def __init__ (self):
        """ Desc and options are initialized empty. """
        self.desc = {}
        self.options = {}
        self.optList = []

    def __str__ (self):
        result = '    <section>\n'
        for opt in self.options.values ():
            result = result + '        ' + str(opt) + '\n'
        result = result + '    </section>'
        return result

    def getDesc (self, preferredLangs):
        return GetDesc (self.desc, preferredLangs)

class DriverInfo:
    """ Maintains a list of option sections and options in them. """
    def startElement (self, name, attr):
        """ Handle start_element events from XML parser. """
        if name == "section":
            self.curOptSection = OptSection ()
            self.optSections.append (self.curOptSection)
        elif name == "option":
            if self.curOptSection == None:
                raise XMLError ("option outside a section")
            if not attr.has_key ("name") or not attr.has_key ("type") or \
               not attr.has_key ("default"):
                raise XMLError ("mandatory option attribute missing")
            if attr.has_key ("valid"):
                self.curOption = OptInfo (attr["name"], attr["type"],
                                          attr["default"], attr["valid"])
            else:
                self.curOption = OptInfo (attr["name"], attr["type"],
                                          attr["default"])
            self.curOptSection.options[attr["name"]] = self.curOption
            self.curOptSection.optList.append (self.curOption)
        elif name == "description":
            if not attr.has_key ("lang") or not attr.has_key ("text"):
                raise XMLError ("description attribute missing")
            if self.curOption != None:
                self.curOptDesc = OptDesc(attr["lang"], attr["text"])
                self.curOption.desc[attr["lang"]] = self.curOptDesc
            elif self.curOptSection != None:
                self.curOptSection.desc[attr["lang"]] = attr["text"]
            else:
                raise XMLError ("description outside an option or section")
        elif name == "enum":
            if not attr.has_key ("value") or not attr.has_key ("text"):
                raise XMLError ("enum attribute missing")
            if self.curOptDesc != None:
                value = attr["value"]
                if not self.curOption.validate (value):
                    raise XMLError ("enum value is out of valid range")
                else:
                    value = StrToValue (value, self.curOption.type)
                self.curOptDesc.enums[value] = attr["text"]
            else:
                raise XMLError ("enum outside an option description")

    def endElement (self, name):
        """ Handle end_element events from XML parser. """
        if name == "section":
            self.curOptSection = None
        elif name == "option":
            self.curOption = None
        elif name == "description":
            self.curOptDesc = None

    def __init__ (self, name):
        """ Obtain and parse config info for this driver.

        Raises a DRIError if the driver does not support configuration.

        Raises a XMLError if the config info is illegal. """
        self.name = name
        driInfo = XDriInfo ("options " + name)

        self.optSections = []
        self.curOptSection = None
        self.curOption = None
        self.curOptDesc = None
        p = xml.parsers.expat.ParserCreate()

        p.StartElementHandler = self.startElement
        p.EndElementHandler = self.endElement

        try:
            p.Parse (driInfo)
        except xml.parsers.expat.ExpatError:
            raise XMLError ("ExpatError")

    def __str__ (self):
        result = '<driconf>\n'
        for sect in self.optSections:
            result = result + str(sect) + '\n'
        result = result + '</driconf>\n'
        return result

class ScreenInfo:
    """ References a DriverInfo object with the real config info. """
    def __init__ (self, screen, dpy = None):
        """ Find or create the driver for this screen.

        Raises a DRIError if the screen is not direct rendering capable or
        the driver does not support configuration.

        Raises a XMLError if the config info is illegal. """
        self.num = screen
        driverName = XDriInfo ("driver " + str(screen), dpy)
        self.driver = GetDriver (driverName, 0)

class DisplayInfo:
    """ Maintains config info for all screens and drivers on a display """
    drivers = {}

    def __init__ (self, dpy = None):
        """ Find all direct rendering capable screens on dpy. """
        self.dpy = dpy
        nScreens = int(XDriInfo ("nscreens", dpy))
        self.screens = [None for i in range (nScreens)]
        for i in range (nScreens):
            self.getScreen (i)

    def getScreen (self, i):
        if i < 0 or i >= len(self.screens):
            return None
        if self.screens[i] != None:
            return self.screens[i]
        try:
            screen = ScreenInfo (i, self.dpy)
        except DRIError:
            screen = None
        self.screens[i] = screen
        return screen

def GetDriver (name, catch=1):
    if DisplayInfo.drivers.has_key (name):
        return DisplayInfo.drivers[name]
    try:
        driver = DriverInfo (name)
    except DRIError, problem:
        if catch:
            driver = None
        else:
            raise DRIError (problem)
    else:
        DisplayInfo.drivers[name] = driver
    return driver

class AppConfig:
    """ Configuration data of an application given by the executable name.

    If no executable name is specified it applies to all applications. """
    def __init__ (self, device, name, executable = None):
        self.device = device
        self.name = name
        self.executable = executable
        self.options = {}

    def __str__ (self):
        result = '        <application name="' + self.name + '"'
        if self.executable:
            result = result + ' executable="' + self.executable + '">\n'
        else:
            result = result + '>\n'
        for n, v in self.options.items ():
            result = result + '            <option name="' + n + \
                     '" value="' + v + '" />\n'
        result = result + '        </application>'
        return result

class DeviceConfig:
    """ Configuration data of a device given by screen and/or driver.

    If neither screen nor driver is specified it applies to all devices. """
    def __init__ (self, config, screen = None, driver = None):
        self.config = config
        self.screen = screen
        self.driver = driver
        self.apps = []

    def __str__ (self):
        result = '    <device'
        if self.screen:
            result = result + ' screen="' + self.screen + '"'
        if self.driver:
            result = result + ' driver="' + self.driver + '"'
        result = result + '>\n'
        for a in self.apps:
            result = result + str(a) + '\n'
        result = result + '    </device>'
        return result

class DRIConfig:
    """ Configuration object representing one configuration file. """
    def startElement (self, name, attr):
        """ Handle start_element events from XML parser. """
        if name == "device":
            if attr.has_key ("screen") and attr.has_key ("driver"):
                self.curDevice = DeviceConfig (self, attr["screen"], attr["driver"])
            elif attr.has_key ("screen"):
                self.curDevice = DeviceConfig (self, screen = attr["screen"])
            elif attr.has_key ("driver"):
                self.curDevice = DeviceConfig (self, driver = attr["driver"])
            else:
                self.curDevice = DeviceConfig (self)
            self.devices.append (self.curDevice)
        elif name == "application":
            if self.curDevice == None:
                raise XMLError ("application outside a device")
            if not attr.has_key ("name"):
                raise XMLError ("mandatory application attribute missing")
            if attr.has_key ("executable"):
                self.curApp = AppConfig (self.curDevice, attr["name"],
                                         attr["executable"])
            else:
                self.curApp = AppConfig (self.curDevice, attr["name"])
            self.curDevice.apps.append (self.curApp)
        elif name == "option":
            if self.curApp == None:
                raise XMLError ("option outside an application")
            if not attr.has_key ("name") or not attr.has_key ("value"):
                raise XMLError ("option attribute missing")
            self.curApp.options[attr["name"]] = attr["value"]

    def endElement (self, name):
        """ Handle end_element events from XML parser. """
        if name == "device":
            self.curDevice = None
        elif name == "application":
            self.curApp = None
    
    def __init__ (self, file, fileName=""):
        """ Parse configuration file. """
        self.devices = []
        self.curDevice = None
        self.curApp = None
        if file:
            self.fileName = file.name
            p = xml.parsers.expat.ParserCreate()
            p.StartElementHandler = self.startElement
            p.EndElementHandler = self.endElement
            try:
                p.ParseFile (file)
            except xml.parsers.expat.ExpatError, problem:
                raise XMLError ("ExpatError " + str(problem))
        else:
            self.fileName = fileName

    def __str__ (self):
        result = '<driconf>\n'
        for d in self.devices:
            result = result + str(d) + '\n'
        result = result + '</driconf>'
        return result
