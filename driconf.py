# DRI configuration GUI using python-gtk

# Copyright (C) 2003-2006  Felix Kuehling

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

import sys
import os
import dri
#import pygtk
from gi import pygtkcompat

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')
from functools import reduce
#pygtk.require ("2.0")
import gtk
import gobject

#if gtk.check_version(2, 4, 0):
#    print("Error: DRIconf requires GTK 2.4 or newer.")
#    sys.exit(1)

import driconf_commonui
import driconf_complexui
import driconf_simpleui

commonui = driconf_commonui     # short cuts
complexui = driconf_complexui
simpleui = driconf_simpleui

from driconf_commonui import _


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "-e":
        expert = True
    else:
        expert = False

    # read configuration information from the drivers
    try:
        commonui.dpy = dri.DisplayInfo ()
    except dri.DRIError as problem:
        dialog = gtk.MessageDialog (None, 0, gtk.MESSAGE_ERROR,
                                    gtk.BUTTONS_OK, str(problem))
        dialog.run()
        dialog.destroy()
        return
    except dri.XMLError as problem:
        dialog = gtk.MessageDialog (
            None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
            _("There are errors in a driver's configuration information:\n"
              "%s\n"
              "This should not happen. It probably means that you have to "
              "update DRIconf.") % str(problem))
        dialog.run()
        dialog.destroy()
        return

    configScreens = [screen for screen in commonui.dpy.screens
                     if screen != None]
    if len(configScreens) == 0:
        dialog = gtk.MessageDialog (
            None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
            _("Could not detect any configurable direct-rendering capable "
              "devices.")+" "+_("DRIconf will be started in expert mode."))
        dialog.run()
        dialog.destroy()
        expert = True

    # read or create configuration files
    fileNameList = ["/etc/drirc", os.path.join (os.environ["HOME"], ".drirc")]
    configList = []
    newFiles = []
    for fileName in fileNameList:
        try:
            cfile = open (fileName, "rb")
        except IOError:
            # Make a default configuration file.
            config = dri.DRIConfig (None, fileName)
            config.writable = True
            for screen in configScreens:
                device = dri.DeviceConfig (config, str(screen.num),
                                           screen.driver.name)
                app = dri.AppConfig (device, "all")
                device.apps.append (app)
                config.devices.append (device)
            # Try to write the new file. If it fails, don't add this config.
            try:
                file = open (config.fileName, "w")
            except IOError:
                config = None
            else:
                file.write (str(config))
                file.close()
                newFiles.append (fileName)
        else:
            # Try to parse the configuration file.
            try:
                config = dri.DRIConfig (cfile)
            except dri.XMLError as problem:
                dialog = gtk.MessageDialog (
                    None, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                    _("Configuration file \"%s\" contains errors:\n"
                      "%s\n"
                      "I will leave the file alone until you fix the problem "
                      "manually or remove the file.") %
                    (fileName, str(problem)))
                dialog.run()
                dialog.destroy()
                continue
            else:
                # Check if the file is writable in the end.
                config.writable = commonui.fileIsWritable (fileName)
            cfile.close()
        if config:
            configList.append (config)

    if len(configList) == 0:
        dialog = gtk.MessageDialog (
            None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
            _("There are no usable DRI configuration files and a new one "
              "could not be created. Exiting now."))
        dialog.run()
        dialog.destroy()
        return

    # open the main window
    if expert:
        complexui.start(configList)
    else:
        simpleui.start(configList)

    if len(newFiles) == 1:
        dialog = gtk.MessageDialog (
            commonui.mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
            _("Created a new DRI configuration file \"%s\" for you.")
            % newFiles[0])
        dialog.run()
        dialog.destroy()
    elif len(newFiles) > 1:
        dialog = gtk.MessageDialog (
            commonui.mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
            _("Created new DRI configuration files %s for you.") %
            reduce(lambda a, b: str(a) + ", " + str(b),
                   ["\"%s\"" % str(a) for a in newFiles]))
        dialog.run()
        dialog.destroy()

    # run
    gtk.main()
