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
from gi import pygtkcompat

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')
#import pygtk
#pygtk.require ("2.0")
import gtk
import gobject

import driconf_commonui
import driconf_complexui
import driconf_appdb
commonui = driconf_commonui    # short cut
complexui = driconf_complexui
appdb = driconf_appdb

from driconf_commonui import _, lang

def isUserConfig(config):
    return config.fileName.startswith(os.environ["HOME"])

def getUserConfig(configList):
    userConfigs = [config for config in configList if isUserConfig(config)]
    if not userConfigs:
        return None
    else:
        return userConfigs[0]

def genNormalDeviceConfigs (configList, dpy):
    """ Generate a list of normalized device configurations.

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
    userConfig = getUserConfig(configList)
    if not userConfig:
        return []
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
            for opt in list(sect.options.values()):
                defaultApp.options[opt.name] = dri.ValueToStr(opt.default, opt.type)
        deviceConfig.isNormalized = True
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
                    for opt,value in list(app.options.items()):
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

def removeRedundantDevices (config, normalDeviceConfigs, onlyTest = False):
    """ Remove device configurations that are redundant ...

    ... after appending normalized device configurations. If onlyTest
    is True, the configuration file is not modified and this function
    returns True iff there are redundant device sections. Otherwise
    False is returned. """
    screens = [device.screen for device in normalDeviceConfigs]
    # Iterate over a copy of the device list, so that devices can be
    # removed safely.
    for device in config.devices[:]:
        if not (hasattr(device, "isNormalized") and device.isNormalized) and \
               device.screen != None and device.driver != None:
            # See if there is a normalized device configuration for
            # this device. In that case this section is redundant.
            try:
                i = screens.index(device.screen)
            except ValueError:
                pass
            else:
                if normalDeviceConfigs[i].driver == device.driver:
                    if onlyTest:
                        return True
                    # Remove redundant device section
                    config.devices.remove(device)
                    config.isModified = True
    return False

def isRedundant (configList, dpy, normalDeviceConfigs = None):
    """ Check if the user configuration is redundant.

    Returns True iff there is a user configuration file that would
    contain redundant device configurations after appending
    normalDeviceConfigs. """
    userConfig = getUserConfig(configList)
    if not userConfig:
        return False
    if normalDeviceConfigs == None:
        normalDeviceConfigs = genNormalDeviceConfigs (configList, dpy)
    return removeRedundantDevices (userConfigs, normalDeviceConfigs,
                                   onlyTest=True)

def isNormalized(configList, dpy, normalDeviceConfigs = None):
    """ Check if the user configuration file is normalized ...

    ... in a set of configuration files, that is if the user
    configuration file would be the same (except for names) after
    normalization. If the user configuration file is normalized, a
    list of existing normalized device configurations is returned. If
    there is no user configuration file, an empty list is
    returned. Otherwise, if there is a user configuration file that is
    not normalized, this function returns None."""
    userConfig = getUserConfig(configList)
    if not userConfig:
        return []
    userDevs = userConfig.devices
    # Find a consistent list of specific device configurations at the
    # end of the user configuration file.
    i = len(userDevs) - 1
    while i >= 0 and userDevs[i].screen != None and userDevs[i].driver != None:
        i = i - 1
    i = i + 1
    specificDevs = userDevs[i:]
    # Make sure there is at least one for each configurable screen.
    # If there are several the last one counts.
    screens = [screen for screen in dpy.screens if screen]
    screenDevs = [None for i in range(len(screens))]
    for device in specificDevs:
        screenNum = int(device.screen)
        if screenNum >= len(screenDevs):
            continue
        if screens[screenNum].driver.name == device.driver:
            screenDevs[screenNum] = device
    if [None for device in screenDevs if device == None]:
        return None  # There are unconfigured screens
    if normalDeviceConfigs == None:
        normalDeviceConfigs = genNormalDeviceConfigs (configList, dpy)
    # Compare existing normalized device configs with generated
    # ones. If they are equivalent, the configuration file is
    # normalized.
    for device,normalDev in zip (screenDevs,normalDeviceConfigs):
        # Check that the first executable is None and that each
        # executable is configured exactly once.
        executables = [app.executable for app in device.apps]
        if not executables or executables[0] != None:
            return None
        del executables[0]
        if [None for exe in executables if exe == None]:
            return None
        executables.sort()
        normalExes = [app.executable for app in normalDev.apps]
        del normalExes[0]
        normalExes.sort()
        if normalExes != executables:
            return None
        # Now check that each application contains the same option settings
        # as the generated normalized configuration
        for normalApp in normalDev.apps:
            app = [dApp for dApp in device.apps
                   if dApp.executable == normalApp.executable][0]
            if app.options != normalApp.options:
                return None
    # The configuration is normalized. Return the list of normalized device
    # configurations from the user configuration files.
    return screenDevs

def normalizeConfig(configList, dpy):
    """ Normalize the user configuration file (if it exists) ...

    ... by appending normalized device configurations for each
    installed device and removing redundant device configurations. If
    the user configuration file is already normalized, only existing
    normalized device configurations are marked as such and redundant
    device configurations are removed. """
    newDeviceConfigs = genNormalDeviceConfigs (configList, dpy)
    existingDeviceConfigs = isNormalized (configList, dpy, newDeviceConfigs)
    if not existingDeviceConfigs and not newDeviceConfigs:
        return []
    userConfig = getUserConfig(configList)
    if existingDeviceConfigs:
        # is already normalized, mark existing normalized device
        # configurations as such.
        for deviceConfig in existingDeviceConfigs:
            deviceConfig.isNormalized = True
        deviceConfigs = existingDeviceConfigs
    elif newDeviceConfigs:
        userConfig.devices.extend(newDeviceConfigs)
        userConfig.isModified = True
        deviceConfigs = newDeviceConfigs
    # Remove redundant device configurations from the user
    # configuration file
    removeRedundantDevices (userConfig, deviceConfigs)
    return deviceConfigs

def lineWrap (string, chars=30):
    head = ""
    tail = string
    while len(tail):
        if len(tail) <= chars:
            return head + tail
        else:
            i = chars
            while i >= chars/3:
                if tail[i] == ' ':
                    j = i + 1
                    break
                elif tail[i] == '-':
                    i = i + 1
                    j = i
                    break
                i = i - 1
            if i < chars/3:
                i = chars
            head, tail = head + tail[:i] + '\n', tail[j:]
    return head

class AppDialog (gtk.Dialog):
    def __init__ (self, title, parent, app=None):
        gtk.Dialog.__init__(self, title, parent,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            ("gtk-ok", gtk.RESPONSE_OK,
                             "gtk-cancel", gtk.RESPONSE_CANCEL))
        self.set_resizable(False)
        table = gtk.Table(3, 2)
        nameLabel = gtk.Label(_("Application Name"))
        nameLabel.show()
        table.attach(nameLabel, 0, 1, 0, 1, 0, gtk.EXPAND, 10, 5)
        self.nameEntry = gtk.Entry()
        if app:
            self.nameEntry.set_text(app.name)
        self.nameEntry.connect("activate",
                               lambda widget: self.response(gtk.RESPONSE_OK))
        self.nameEntry.show()
        table.attach(self.nameEntry, 1, 2, 0, 1,
                     gtk.EXPAND|gtk.FILL, gtk.EXPAND, 10, 5)

        execLabel = gtk.Label(_("Executable Name"))
        execLabel.show()
        table.attach(execLabel, 0, 1, 1, 2, 0, gtk.EXPAND, 10, 5)
        self.execEntry = gtk.Entry()
        if app:
            self.execEntry.set_text(app.executable)
        self.execEntry.connect("activate",
                               lambda widget: self.response(gtk.RESPONSE_OK))
        self.execEntry.show()
        table.attach(self.execEntry, 1, 2, 1, 2,
                     gtk.EXPAND|gtk.FILL, gtk.EXPAND, 10, 5)
        hBox = gtk.HBox(spacing=10)
        infoImageVBox = gtk.VBox()
        infoImage = commonui.StockImage(gtk.STOCK_DIALOG_INFO,
                                        gtk.ICON_SIZE_DIALOG)
        infoImage.show()
        infoImageVBox.pack_start(infoImage, False, False, 0)
        infoImageVBox.show()
        hBox.pack_start(infoImageVBox, False, False, 0)
        infoLabel = gtk.Label(_(
            "The executable name is important for identifying the "
            "application. If you get it wrong, your settings will not "
            "apply. Beware that some applications are started by a "
            "shell script, that has a different name than the real "
            "executable."))
        # TODO: Add a small database of known applications with their
        # executable names that can be picked from a menu.
        infoLabel.set_line_wrap (True)
        infoLabel.show()
        hBox.pack_start(infoLabel, False, False, 0)
        hBox.show()
        table.attach (hBox, 0, 2, 2, 3,
                      gtk.EXPAND|gtk.FILL, gtk.EXPAND, 10, 5)
        table.show()
        self.vbox.pack_start(table, True, True, 5)
        self.show()
        self.nameEntry.grab_focus()

    def getName (self):
        return self.nameEntry.get_text()

    def getExecutable (self):
        return self.execEntry.get_text()

class AppPage (gtk.ScrolledWindow):
    def __init__ (self, driver, app):
        """ Constructor. """
        gtk.ScrolledWindow.__init__ (self)
        self.set_policy (gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.driver = driver
        self.app = app
        #self.tooltips = gtk.Tooltips() #TODO: tooltip
        self.table = None
        self.refreshOptions()

    def refreshOptions (self):
        if self.table:
            self.remove(self.get_child())
        self.optLines = []
        self.table = gtk.Table(len(self.app.options)+1, 3)
        self.add_with_viewport(self.table)
        self.optionTree = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_INT)
        i = 0
        sectI = 0
        for sect in self.driver.optSections:
            sectIter = self.optionTree.append(None, [
                lineWrap(sect.getDesc([lang])), sectI, -1])
            sectHasOpts = False
            optI = 0
            for opt in sect.optList:
                if opt.name in self.app.options:
                    self.optLines.append(
                        commonui.OptionLine(self, i, opt, True, True))
                    i = i + 1
                else:
                    self.optionTree.append(sectIter, [
                        lineWrap(opt.getDesc([lang]).text), sectI, optI])
                    sectHasOpts = True
                optI = optI + 1
            if not sectHasOpts:
                self.optionTree.remove(sectIter)
            sectI = sectI + 1
        if len(self.optionTree) > 0:
            addLabel = commonui.WrappingDummyCheckButton(_("Add setting"),
                                                         width=200)
            addLabel.show()
            self.table.attach(addLabel, 0, 1, i, i+1, gtk.EXPAND|gtk.FILL, 0, 5, 5)
            addCombo = gtk.ComboBox() #self.optionTree) #TODO
            addCombo.connect("changed", self.addOption)
            cell = gtk.CellRendererText()
            addCombo.pack_start(cell, True)
            addCombo.add_attribute(cell, 'text', 0)
            addCombo.show()
            self.table.attach(addCombo, 1, 2, i, i+1, gtk.FILL, 0, 5, 5)
        self.table.show()

    def optionModified (self, optLine):
        self.app.modified(self.app)

    def removeOption (self, optLine, opt):
        del self.app.options[opt.name]
        self.refreshOptions()
        self.app.modified(self.app)

    def addOption (self, combo):
        activeIter = combo.get_active_iter()
        if not activeIter:
            # Got triggered by the set_active(-1) below.
            return
        sectI = self.optionTree.get_value(activeIter, 1)
        optI  = self.optionTree.get_value(activeIter, 2)
        if optI < 0:
            combo.set_active(-1)
            return
        opt = self.driver.optSections[sectI].optList[optI]
        self.app.options[opt.name] = dri.ValueToStr(opt.default, opt.type)
        self.refreshOptions()
        self.app.modified(self.app)
    
    def doValidate (self):
        pass

    def commit (self):
        for optLine in self.optLines:
            name = optLine.opt.name
            value = optLine.getValue()
            if value == None and name in self.app.options:
                del self.app.options[name]
            elif value != None:
                self.app.options[name] = value

class MainWindow (gtk.Window):
    def __init__ (self, configList):
        gtk.Window.__init__(self)
        self.set_title(_("Direct Rendering Preferences"))
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_border_width(10)
        self.connect("destroy", lambda dummy: gtk.main_quit())
        self.connect("delete_event", self.exitHandler)
        self.configList = configList # Remember for switching to expert mode
        self.userConfig = getUserConfig(configList)
        self.screens = [screen for screen in commonui.dpy.screens if screen]
        self.vbox = gtk.VBox(spacing=10)
        if len(self.screens) > 1:
            self.deviceCombo = gtk.combo_box_new_text()
            for screen in self.screens:
                if screen.glxInfo:
                    self.deviceCombo.append_text(_("Screen") + " %d: %s (%s)" % (
                        screen.num, screen.glxInfo.renderer, screen.glxInfo.vendor))
                else:
                    self.deviceCombo.append_text(_("Screen") + " %d: %s" % (
                        screen.num, screen.driver.name.capitalize()))
            self.deviceCombo.set_active(0)
            self.deviceCombo.connect("changed", self.changeDevice)
            self.deviceCombo.show()
            self.vbox.pack_start(self.deviceCombo, False, False, 0)
        else:
            screen = self.screens[0]
            if screen.glxInfo:
                text = "%s (%s)" % (
                    screen.glxInfo.renderer, screen.glxInfo.vendor)
            else:
                text = _("Screen") + " %d: %s" % (
                    screen.num, screen.driver.name.capitalize())
            deviceHBox = gtk.HBox()
            deviceLabel = gtk.Label()
            deviceLabel.set_justify(gtk.JUSTIFY_LEFT)
            deviceLabel.set_markup("<b>" + commonui.escapeMarkup(text) + "</b>")
            deviceLabel.show()
            deviceHBox.pack_start(deviceLabel, False, False, 0)
            deviceHBox.show()
            self.vbox.pack_start(deviceHBox, False, False, 0)
        buttonBox = gtk.HButtonBox()
        buttonBox.set_spacing(10)
        buttonBox.set_layout(gtk.BUTTONBOX_END)
        expertButton = gtk.Button()
        expertHBox = gtk.HBox()
        expertImage = commonui.StockImage("gtk-jump-to", gtk.ICON_SIZE_BUTTON)
        expertImage.show()
        expertHBox.pack_start(expertImage)
        expertLabel = gtk.Label(_("Expert Mode"))
        expertLabel.show()
        expertHBox.pack_start(expertLabel)
        expertHBox.show()
        expertButton.add(expertHBox)
        expertButton.connect("clicked", self.expertHandler)
        expertButton.show()
        buttonBox.add(expertButton)
        closeButton = gtk.Button(stock="gtk-close")
        closeButton.connect("clicked", lambda dummy: gtk.main_quit())
        closeButton.show()
        buttonBox.add(closeButton)
        aboutButton = gtk.Button(stock="gtk-about")
        aboutButton.connect("clicked", self.aboutHandler)
        aboutButton.show()
        buttonBox.add(aboutButton)
        buttonBox.set_child_secondary(aboutButton, True)
        buttonBox.show()
        self.vbox.pack_end(buttonBox, False, False, 0)
        self.expander = gtk.Expander() #"<b>" + commonui.escapeMarkup(_("Application settings")) + "</b>")
        self.expander.set_use_markup(True)
        self.expander.connect("activate", self.expanderChanged)
        self.expander.show()
        self.vbox.pack_end(self.expander, False, True, 0)
        self.expanderVBox = gtk.VBox(spacing=10)
        self.appButtonBox = gtk.HBox()
        self.appRemoveButton = gtk.Button(stock="gtk-remove")
        self.appRemoveButton.connect("clicked", self.removeApp)
        self.appRemoveButton.show()
        self.appButtonBox.pack_end(self.appRemoveButton, False, False, 0)
        self.appPropButton = gtk.Button(stock="gtk-properties")
        self.appPropButton.connect("clicked", self.appProperties)
        self.appPropButton.show()
        self.appButtonBox.pack_end(self.appPropButton, False, False, 0)
        self.appButtonBox.show()
        self.expanderVBox.pack_start(self.appButtonBox, False, False, 0)
        self.expanderVBox.show()
        self.expander.add(self.expanderVBox)
        self.notebook = None
        self.appCombo = None
        self.appNotebook = None
        self.appPage = None
        self.selectScreen(0)
        self.vbox.show()
        self.add(self.vbox)

    def selectScreen (self, n):
        self.curScreen = self.screens[n]
        # Find that device's configuration in the user config. Search
        # from the end, because that's where the normalized configs are.
        self.deviceConfig = None
        i = len(self.userConfig.devices)-1
        while i >= 0 and self.userConfig.devices[i].screen != None and \
              self.userConfig.devices[i].driver != None:
            if self.curScreen.num == int(self.userConfig.devices[i].screen) and \
               self.curScreen.driver.name == self.userConfig.devices[i].driver:
                self.deviceConfig = self.userConfig.devices[i]
                self.driver = self.curScreen.driver
                break
            i = i - 1
        # Sanity checks. These should all be true after normalization.
        assert(self.deviceConfig)
        assert(self.deviceConfig.isNormalized)
        assert(len(self.deviceConfig.apps) > 0 and
               self.deviceConfig.apps[0].executable == None)
        # Register modified callback
        self.deviceConfig.apps[0].modified = self.configModified
        # Build UI for the screen configuration
        if self.notebook:
            self.vbox.remove(self.notebook)
        self.notebook = gtk.Notebook()
        self.notebook.popup_enable()
        self.sectPages = []
        self.sectLabels = []
        unknownPage = commonui.UnknownSectionPage (self.driver,
                                                   self.deviceConfig.apps[0])
        if len(unknownPage.opts) > 0:
            unknownPage.show()
            unknownLabel = gtk.Label (_("Unknown options"))
            unknownLabel.show()
            self.notebook.append_page (unknownPage, unknownLabel)
            self.sectPages.append (unknownPage)
            self.sectLabels.append (unknownLabel)
        for sect in self.driver.optSections:
            sectPage = commonui.SectionPage (sect, self.deviceConfig.apps[0],
                                             True)
            sectPage.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
            sectPage.show()
            desc = sect.getDesc([lang])
            if desc:
                sectLabel = gtk.Label (desc)
                sectLabel.set_line_wrap (True)
            else:
                sectLabel = gtk.Label (_("(no description)"))
            sectLabel.show()
            self.notebook.append_page (sectPage, sectLabel)
            self.sectPages.append (sectPage)
            self.sectLabels.append (sectLabel)
        if len(self.sectLabels) > 0:
            style = self.sectLabels[0].get_style()
            #self.default_normal_fg = style.fg[gtk.STATE_NORMAL].copy()
            #self.default_active_fg = style.fg[gtk.STATE_ACTIVE].copy() #TODO
        self.validate()
        self.notebook.show()
        self.vbox.pack_start(self.notebook, True, True, 0)
        if self.appCombo:
            self.appButtonBox.remove(self.appCombo)
        self.appTree = appdb.createTreeStore()
        self.appTree.prepend(None, ["- - - - - - - - - - - - - - - -", "", appdb.SEPARATOR])
        for i in range(1,len(self.deviceConfig.apps)):
            self.appTree.insert(None, i-1, [self.deviceConfig.apps[i].name,
                                            self.deviceConfig.apps[i].executable,
                                            i])
        self.appTree.append(None,
                            [_("Other application ..."), "", appdb.CUSTOM_APP])
        self.appCombo = gtk.ComboBox()#self.appTree) #TODO: combobox
        if hasattr(self.appCombo, "set_row_separator_func"):
            # Available as of gtk 2.6
            self.appCombo.set_row_separator_func(appdb.isSeparator)
        cell = gtk.CellRendererText()
        self.appCombo.pack_start(cell, True)
        self.appCombo.add_attribute(cell, 'text', 0)
        if len(self.deviceConfig.apps) > 1:
            self.appCombo.set_active(0)
            self.expander.set_expanded(True)
            self.vbox.set_child_packing(self.expander, True, True,
                                        0, gtk.PACK_END)
            self.appPropButton.set_sensitive(True)
            self.appRemoveButton.set_sensitive(True)
        else:
            self.expander.set_expanded(False)
            self.vbox.set_child_packing(self.expander, False, True,
                                        0, gtk.PACK_END)
            self.appPropButton.set_sensitive(False)
            self.appRemoveButton.set_sensitive(False)
        self.appCombo.connect("changed", self.changeApp)
        self.appCombo.show()
        self.appButtonBox.pack_start(self.appCombo, True, True, 0)
        if len(self.deviceConfig.apps) > 1:
            self.selectApp(self.deviceConfig.apps[1])
        else:
            self.selectApp(None)

    def selectApp (self, app):
        if self.appNotebook:
            self.expanderVBox.remove(self.appNotebook)
            self.appNotebook = None
            self.appPage = None
        elif self.appPage:
            self.expanderVBox.remove(self.appPage)
            self.appPage = None
        if not app:
            self.appPropButton.set_sensitive(False)
            self.appRemoveButton.set_sensitive(False)
            return
        self.appPropButton.set_sensitive(True)
        self.appRemoveButton.set_sensitive(True)
        app.modified = self.configModified
        unknownPage = commonui.UnknownSectionPage (self.driver,
                                                   app)
        if len(unknownPage.opts) > 0:
            self.appNotebook = gtk.Notebook()
            self.appNotebook.popup_enable()
            unknownPage.show()
            unknownLabel = gtk.Label (_("Unknown options"))
            unknownLabel.show()
            self.appNotebook.append_page (unknownPage, unknownLabel)
            self.appPage = AppPage (self.driver, app)
            self.appPage.show()
            appPageLabel = gtk.Label (_("Known options"))
            appPageLabel.show()
            self.appNotebook.append_page (self.appPage, appPageLabel)
            self.appNotebook.show()
            appWidget = self.appNotebook
        else:
            self.appPage = AppPage (self.driver, app)
            self.appPage.show()
            appWidget = self.appPage
        self.expanderVBox.pack_start (appWidget, True, True, 0)

    def validate (self):
        """ Validate the configuration.

        Labels of invalid section pages are highlighted. Returns whether
        there were invalid option values. """
        index = 0
        allValid = True
        for sectPage in self.sectPages:
            valid = sectPage.validate()
            if not valid:
                # strange, active and normal appear to be swapped :-/
                self.sectLabels[index].modify_fg (
                    gtk.STATE_NORMAL, gtk.gdk.Color (65535, 0, 0))
                self.sectLabels[index].modify_fg (
                    gtk.STATE_ACTIVE, gtk.gdk.Color (65535, 0, 0))
            else:
                pass #TODO
                #self.sectLabels[index].modify_fg (
                #    gtk.STATE_NORMAL, self.default_normal_fg)
                #self.sectLabels[index].modify_fg (
                #    gtk.STATE_ACTIVE, self.default_active_fg)
            allValid = allValid and valid
            index = index+1
        return allValid        

    def commit (self):
        for sectPage in self.sectPages:
            sectPage.commit()
        if self.appPage:
            self.appPage.commit()

    def changeDevice (self, combo):
        self.selectScreen(combo.get_active())

    def changeApp (self, combo):
        it = combo.get_active_iter()
        if it != None:
            name, executable, index = self.appTree.get(
                it, appdb.COL_NAME, appdb.COL_EXEC, appdb.COL_INDEX)
        else:
            index = 0
        if index > 0:
            # Select an existing application
            app = self.deviceConfig.apps[index]
            if self.appPage:
                lastApp = self.appPage.app
            else:
                lastApp = None
            if app != lastApp:
                if lastApp:
                    self.appPage.commit()
                self.selectApp(app)
        elif index == 0:
            # Deselect application
            if self.appPage:
                self.appPage.commit()
            self.selectApp(None)
        elif index == appdb.PREDEF_APP:
            # Add new pre-defined application
            self.addPredefApp(name, executable)
        else:
            # Keep (restore) selection
            if self.appPage:
                i = self.deviceConfig.apps.index(self.appPage.app)-1
            else:
                i = -1
            self.appCombo.set_active(i)
            if index == appdb.CUSTOM_APP:
                # Add a user-defined application
                self.addUserdefApp()

    def expanderChanged (self, expander):
        # This signal handler seems to get called before the expander
        # state is changed. So the logic is reversed.
        if not self.expander.get_expanded():
            self.vbox.set_child_packing(self.expander, True, True,
                                        0, gtk.PACK_END)
        else:
            self.vbox.set_child_packing(self.expander, False, True,
                                        0, gtk.PACK_END)

    def checkAppProperties (self, dialog, name, executable, sameApp=None):
        errorStr = None
        if name == "" or executable == "":
            # Error message
            errorStr = _("You must enter both an application name and "
                         "an executable name.")
        else:
            for app in self.deviceConfig.apps:
                if app != sameApp and name == app.name:
                    errorStr = _("There exists an application "
                                 "configuration with the same name. "
                                 "Please enter a different name.")
                    break
                elif app != sameApp and executable == app.executable:
                    errorStr = _("There exists an application "
                                 "configuration for the same "
                                 "executable. You can't create multiple "
                                 "application configurations for the "
                                 "same executable.")
                    break
        if errorStr:
            dialog = gtk.MessageDialog(
                dialog, gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, errorStr)
            dialog.run()
            dialog.destroy()
            return False
        return True

    def doAddApp (self, name, executable):
        app = dri.AppConfig(self.deviceConfig, name, executable)
        self.deviceConfig.apps.append(app)
        i = len(self.deviceConfig.apps)-1
        self.appTree.insert(None, i-1, [name, executable, i])
        self.appCombo.set_active(i-1)
        self.configModified (self.deviceConfig)

    def addUserdefApp (self):
        dialog = AppDialog(_("Add Application"), self)
        done = False
        while not done:
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                name = dialog.getName().strip()
                executable = dialog.getExecutable().strip()
                if self.checkAppProperties (dialog, name, executable):
                    self.doAddApp(name, executable)
                    done = True
            else:
                done = True
        dialog.destroy()

    def addPredefApp (self, name, executable):
        # Check for existing apps with same name or executable
        i = 0
        for app in self.deviceConfig.apps:
            if app.name == name or app.executable == executable:
                # Select that app instead of creating a new one
                if self.appPage:
                    lastApp = self.appPage.app
                else:
                    lastApp = None
                if app != lastApp:
                    if lastApp:
                        self.appPage.commit()
                    self.selectApp(app)
                self.appCombo.set_active(i)
                return
            i = i + 1
        self.doAddApp (name, executable)

    def appProperties (self, button):
        if not self.appPage:
            return
        dialog = AppDialog(_("Application Properties"), self, self.appPage.app)
        done = False
        while not done:
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                name = dialog.getName().strip()
                executable = dialog.getExecutable().strip()
                if self.checkAppProperties (dialog, name, executable,
                                            self.appPage.app):
                    i = self.deviceConfig.apps.index(self.appPage.app)
                    it = self.appTree.get_iter((i-1,))
                    self.appTree.set(it,
                                     appdb.COL_NAME, name,
                                     appdb.COL_EXEC, executable,
                                     appdb.COL_INDEX, i)
                    #self.appCombo.remove_text(i-1)
                    #self.appCombo.insert_text(i-1, name)
                    #self.appCombo.set_active(i-1)
                    self.appPage.app.name = name
                    self.appPage.app.executable = executable
                    self.configModified (self.appPage.app)
                    done = True
            else:
                done = True
        dialog.destroy()

    def removeApp (self, button):
        if not self.appPage:
            return
        i = self.deviceConfig.apps.index(self.appPage.app)
        it = self.appTree.get_iter((i-1,))
        if i+1 < len(self.deviceConfig.apps):
            newI = i
            newApp = self.deviceConfig.apps[i+1]
        elif i > 1:
            newI = i-1
            newApp = self.deviceConfig.apps[i-1]
        else:
            newI = 0
            newApp = None
        del self.deviceConfig.apps[i]
        self.selectApp(newApp)
        # Adjust indices of all subsequent rows
        jt = self.appTree.iter_next(it)
        while jt != None:
            j = self.appTree.get_value(jt, appdb.COL_INDEX)
            if j <= 0:
                break
            self.appTree.set_value(jt, appdb.COL_INDEX, j-1)
            jt = self.appTree.iter_next(jt)
        self.appTree.remove(it)
        self.appCombo.set_active(newI-1)
        self.configModified(self.deviceConfig)

    def exitHandler (self, widget, event=None):
        # Always ok to destroy the window
        return False

    def aboutHandler (self, widget):
        dialog = commonui.AboutDialog()
        dialog.show()
        dialog.run()
        dialog.destroy()

    def expertHandler (self, widget):
        self.destroy() # triggers main_quit
        complexui.start(self.configList)
        gtk.main()

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
                _("Can't open \"%s\" for writing.") % self.userConfig.fileName)
            dialog.run()
            dialog.destroy()
            self.inConfigModified = False
            return
        self.commit()
        file.write (str(self.userConfig))
        file.close()

    def validateDriverPanel (self):
        self.validate()

def start (configList):
    userConfig = getUserConfig(configList)
    if not userConfig:
        dialog = gtk.MessageDialog (
            None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
            _("The DRI configuration file \"%s\" is broken or could not be "
              "created.") % os.path.join (os.environ["HOME"], ".drirc") +" "+
            _("DRIconf will be started in expert mode."))
        dialog.run()
        dialog.destroy()
        complexui.start(configList)
        return
    if not userConfig.writable:
        # Not writable: start expert mode
        dialog = gtk.MessageDialog (
            None, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
            _("Your DRI configuration file \"%s\" is not writable.") %
            userConfig.fileName +" "+
            _("DRIconf will be started in expert mode."))
        dialog.run()
        dialog.destroy()
        complexui.start(configList)
        return
    normalizedDeviceConfigs = normalizeConfig(configList, commonui.dpy)
    if normalizedDeviceConfigs == None:
        dialog = gtk.MessageDialog (
            None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
            _("Normalization of your DRI configuration file \"%s\" failed. "
              "Please report a bug with the original configuration file "
              "attached. The file will be treated as read-only for now.") %
            userConfig.fileName +" "+
            _("DRIconf will be started in expert mode."))
        dialog.run()
        dialog.destroy()
        userConfig.writable = False
        complexui.start(configList)
        return
    mainWindow = MainWindow(configList)
    commonui.mainWindow = mainWindow
    mainWindow.set_default_size (-1, 500)
    mainWindow.show()
    # Save modified normalized configuration before we start
    if hasattr(userConfig, "isModified") and userConfig.isModified:
        mainWindow.configModified(userConfig)
