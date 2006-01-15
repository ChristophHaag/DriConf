# DRI configuration GUI: simplified UI components

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

import os
import dri
import pygtk
pygtk.require ("2.0")
import gtk
import gobject

import driconf_commonui
commonui = driconf_commonui    # short cut

from driconf_commonui import _, lang, findInShared, escapeMarkup, WrappingCheckButton, SectionPage, UnknownSectionPage

def isUserConfig(config):
    return config.fileName.startswith(os.environ["HOME"])

def genSimpleDeviceConfigs (configList, dpy):
    """ Generate a list of simple device configurations.

    One device configuration for each installed device. Each contains
    a default application configuration that explicitly sets all
    options to their default values in order to override values in
    previous less specific device sections. Then it appends
    application configurations for all application configurations in
    all configuration files that affect the respective device. The
    result is one device configuration per existing device that
    summarizes the entire configuration of existing devices and
    overrides any previous settings.

    If there is no user configuration file, an empty list is returned. """
    userConfigs = [config for config in configList if isUserConfig(config)]
    if not userConfigs:
        return []
    userConfig = userConfigs[0]
    screens = [screen for screen in dpy.screens if screen]
    deviceConfigs = []
    # Create one device configuration for each installed device on this display
    for screen in screens:
        if screen == None:
            continue
        driver = screen.driver
        deviceConfig = dri.DeviceConfig(userConfig, str(screen.num), driver.name)
        defaultApp = dri.AppConfig(deviceConfig, "Default")
        deviceConfig.apps.append(defaultApp)
        for sect in driver.optSections:
            for opt in sect.options.values():
                defaultApp.options[opt.name] = dri.ValueToStr(opt.default, opt.type)
        deviceConfig.isSimplified = True
        deviceConfigs.append(deviceConfig)
    for config in configList:
        configIsUser = isUserConfig(config)
        for device in config.devices:
            # Determine all installed devices affected by this device-section
            # in the original configuration file
            curDeviceConfigs = [deviceConfig for deviceConfig in deviceConfigs
                                if (device.screen == None or
                                    device.screen == deviceConfig.screen)
                                and (device.driver == None or
                                     device.driver == deviceConfig.driver)]
            for curDevice in curDeviceConfigs:
                driver = dpy.getScreen(int(curDevice.screen)).driver
                for app in device.apps:
                    # Determine all applications on this device affected by
                    # this application section in the original config file.
                    # It should be one at most. Create a new application
                    # configuration if needed.
                    curApps = [curApp for curApp in curDevice.apps
                               if app.executable == curApp.executable]
                    assert len(curApps) <= 1
                    if curApps:
                        curApp = curApps[0]
                    else:
                        curApp = dri.AppConfig(curDevice, app.name, app.executable)
                        curDevice.apps.append(curApp)
                    # Update all option settings. Non-existing options
                    # or invalid values are only considered in
                    # redundant device sections.
                    for opt,value in app.options.items():
                        isValid = False
                        if configIsUser and \
                               device.screen != None and device.driver != None:
                            isValid = True
                        else:
                            optInfo = driver.getOptInfo(opt)
                            if optInfo and optInfo.validate(value):
                                isValid = True
                        if isValid:
                            curApp.options[opt] = value
    return deviceConfigs

def removeRedundantDevices (config, simpleDeviceConfigs, onlyTest = False):
    """ Remove device configurations that are redundant ...

    ... after appending simplified device configurations. If onlyTest
    is True, the configuration file is not modified and this function
    returns True iff there are redundant device sections. Otherwise
    False is returned. """
    screens = [device.screen for device in simpleDeviceConfigs]
    for device in config.devices:
        if not (hasattr(device, "isSimplified") and device.isSimplified) and \
               device.screen != None and device.driver != None:
            # See if there is a simplified device configuration for
            # this device. In that case this section is redundant.
            try:
                i = screens.index(device.screen)
            except ValueError:
                pass
            else:
                if simpleDeviceConfigs[i].driver == device.driver:
                    if onlyTest:
                        return True
                    # Remove redundant device section
                    config.devices.remove(device)
                    config.isModified = True
    return False

def isRedundant (configList, dpy, simpleDeviceConfigs = None):
    """ Check if the user configuration is redundant.

    Returns True iff there is a user configuration file that would
    contain redundant device configurations after appending
    simpleDeviceConfigs. """
    userConfigs = [config for config in configList if isUserConfig(config)]
    if not userConfigs:
        return False
    if simpleDeviceConfigs == None:
        simpleDeviceConfigs = genSimpleDeviceConfigs (configList, dpy)
    return removeRedundantDevices (userConfigs[0], simpleDeviceConfigs,
                                   onlyTest=True)

def isSimplified(configList, dpy, simpleDeviceConfigs = None):
    """ Check if the user configuration file is simplified ...

    ... in a set of configuration files, that is if the user
    configuration file would be the same (except for names) after
    simplification. If the user configuration file is simplified, a
    list of existing simple device configurations is returned. If
    there is no user configuration file, an empty list is
    returned. Otherwise, if there is a user configuration file that is
    not simplified, this function returns None. """
    userConfigs = [config for config in configList if isUserConfig(config)]
    if not userConfigs:
        return []
    userDevs = userConfigs[0].devices
    # Find a consistent list of specific device configurations at the
    # end of the user configuration file.
    i = len(userDevs) - 1
    while i >= 0 and userDevs[i].screen != None and userDevs[i].driver != None:
        i = i - 1
    i = i + 1
    specificDevs = userDevs[i:]
    # Make sure there is exactly one for each configurable screen
    screenDevs = [None for i in range(len(dpy.screens))]
    for device in specificDevs:
        screenNum = int(device.screen)
        if screenNum >= len(screenDevs):
            continue
        if dpy.screens[screenNum] != None and \
           dpy.screens[screenNum].driver.name == device.driver:
            if screenDevs[screenNum] != None:
                return None  # More than one device section for this screen
            screenDevs[screenNum] = device
    configurableScreenDevs = [device for i,device in enumerate(screenDevs)
                              if dpy.screens[i] != None]
    if [None for device in configurableScreenDevs if device == None]:
        return None  # There are unconfigured screens
    if simpleDeviceConfigs == None:
        simpleDeviceConfigs = genSimpleDeviceConfigs (configList, dpy)
    # Compare existing simple device configs with generated ones. If
    # they are equivalent, the configuration file is simplified.
    for device,simpleDev in zip (configurableScreenDevs,simpleDeviceConfigs):
        # Check that the first executable is None and that each
        # executable is configured exactly once.
        executables = [app.executable for app in device.apps]
        if not executables or executables[0] != None:
            return None
        del executables[0]
        if [None for exe in executables if exe == None]:
            return None
        executables.sort()
        simpleExes = [app.executable for app in simpleDev.apps]
        del simpleExes[0]
        simpleExes.sort()
        if simpleExes != executables:
            return None
        # Now check that each application contains the same option settings
        # as the generated simplified configuration
        for simpleApp in simpleDev.apps:
            app = [dApp for dApp in device.apps
                   if dApp.executable == simpleApp.executable][0]
            if app.options != simpleApp.options:
                return None
    # The configuration is simplified. Return the list of simplified device
    # configurations from the user configuration files.
    return configurableScreenDevs

def simplifyConfig(configList, dpy):
    """ Simplify the user configuration file (if it exists) ...

    ... by appending simplified device configurations for each
    installed device and removing redundant device configurations. If
    the user configuration file is already simplified, only existing
    simplified device configurations are marked as such and redundant
    device configurations are removed. """
    newDeviceConfigs = genSimpleDeviceConfigs (configList, dpy)
    existingDeviceConfigs = isSimplified (configList, dpy, newDeviceConfigs)
    if not existingDeviceConfigs and not newDeviceConfigs:
        return []
    userConfig = [config for config in configList if isUserConfig(config)][0]
    if existingDeviceConfigs:
        # is already simplified, mark existing simplified device
        # configurations as such.
        for deviceConfig in existingDeviceConfigs:
            deviceConfig.isSimplified = True
        deviceConfigs = existingDeviceConfigs
    elif newDeviceConfigs:
        userConfig.devices.extend(newDeviceConfigs)
        userConfig.isModified = True
        deviceConfigs = newDeviceConfigs
    # Remove redundant device configurations from the user
    # configuration file
    removeRedundantDevices (userConfig, deviceConfigs)
    return deviceConfigs

class MainWindow (gtk.Window):
    def __init__ (self, configList):
        gtk.Window.__init__(self)
        self.set_title ("DRIconf")
        self.connect ("destroy", lambda dummy: gtk.main_quit())
        self.connect ("delete_event", self.exitHandler)

        self.userConfig = [config for config in configList if isUserConfig(config)][0]
        self.screens = [screen for screen in commonui.dpy.screens if screen]
        # Start with screen0
        self.curScreen = self.screens[0]
        # Find that device's configuration in the user config. Search
        # from the end, because that's where the simplified configs are.
        self.deviceConfig = None
        i = len(self.userConfig.devices)-1
        while i >= 0 and self.userConfig.devices[i].screen != None and \
              self.userConfig.devices[i].driver != None:
            if self.curScreen.num == int(self.userConfig.devices[i].screen) and \
               self.curScreen.driver.name == self.userConfig.devices[i].driver:
                self.deviceConfig = self.userConfig.devices[i]
                self.driver = self.curScreen.driver
                break
        assert(self.deviceConfig)
        assert(len(self.deviceConfig.apps) > 0 and
               self.deviceConfig.apps[0].executable == None)
        # Register modified callback
        self.deviceConfig.apps[0].modified = self.configModified

        vbox = gtk.VBox()
        notebook = gtk.Notebook()
        notebook.popup_enable()
        notebook.set_scrollable(True)
        self.sectPages = []
        self.sectLabels = []
        unknownPage = UnknownSectionPage (self.driver, self.deviceConfig.apps[0])
        if len(unknownPage.opts) > 0:
            unknownPage.show()
            unknownLabel = gtk.Label (_("Unknown"))
            unknownLabel.show()
            notebook.append_page (unknownPage, unknownLabel)
            self.sectPages.append (unknownPage)
            self.sectLabels.append (unknownLabel)
        for sect in self.driver.optSections:
            sectPage = SectionPage (sect, self.deviceConfig.apps[0], True)
            sectPage.show()
            desc = sect.getDesc([lang])
            if desc:
                sectLabel = gtk.Label (desc)
                sectLabel.set_line_wrap (True)
            else:
                sectLabel = gtk.Label (_("(no description)"))
            sectLabel.show()
            notebook.append_page (sectPage, sectLabel)
            self.sectPages.append (sectPage)
            self.sectLabels.append (sectLabel)
        if len(self.sectLabels) > 0:
            style = self.sectLabels[0].get_style()
            self.default_normal_fg = style.fg[gtk.STATE_NORMAL].copy()
            self.default_active_fg = style.fg[gtk.STATE_ACTIVE].copy()
        notebook.show()
        vbox.pack_start(notebook)
        vbox.show()
        self.add(vbox)

    def configModified (self, node, b=True):
        if b != True:
            return
        # Save the configuration file
        try:
            file = open (self.userConfig.fileName, "w")
        except IOError:
            dialog = gtk.MessageDialog (
                commonui.mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                _("Can't open \"%s\" for writing.") % config.fileName)
            dialog.run()
            dialog.destroy()
            self.inConfigModified = False
            return
        self.commit()
        file.write (str(self.userConfig))
        file.close()

    def commit (self):
        for sectPage in self.sectPages:
            sectPage.commit()

    def exitHandler (self, widget, event=None):
        # Always ok to destroy the window
        return False
