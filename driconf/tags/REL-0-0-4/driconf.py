# DRI configuration GUI using python-gtk

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
import locale
import dri
from gtk import *
from driconf_xpm import *

class DataPixmap (GtkPixmap):
    def __init__ (self, window, data):
        window.realize()
        style = window.get_style()
        pixmap, mask = create_pixmap_from_xpm_d(window.get_window(),
                                                style.bg[STATE_NORMAL],
                                                data)
        GtkPixmap.__init__ (self, pixmap, mask)

class OptionLine:
    def __init__ (self, page, i, opt):
        self.page = page
        self.opt = opt
        typeString = opt.type
        if opt.valid:
            typeString = typeString+" ["+ \
                         reduce(lambda x,y: x+','+y, map(str,opt.valid))+"]"
        self.check = GtkCheckButton (opt.name)
        self.check.set_active (page.app.options.has_key (opt.name))
        self.check.connect ("clicked", self.checkOpt)
        tooltipString = opt.getDesc([lang]).text + " ("+typeString+")"
        page.tooltips.set_tip (self.check, tooltipString.encode(encoding))
                               
        self.check.show()
        page.table.attach (self.check, 0, 1, i, i+1, EXPAND|FILL, 0, 5, 5)
        if page.app.options.has_key (opt.name):
            try: 
                value = dri.StrToValue (page.app.options[opt.name], opt.type)
            except dri.XMLError:
                value = None
        else:
            value = None
        if value == None:
            value = opt.default
        self.initWidget (opt, value)
        page.table.attach (self.widget, 1, 2, i, i+1, FILL, 0, 5, 5)

    def initWidget (self, opt, value):
        if opt.type == "bool":
            self.toggleLabel = GtkLabel()
            if value:
                self.toggleLabel.set_text ("True")
            else:
                self.toggleLabel.set_text ("False")
            self.toggleLabel.show()
            self.widget = GtkToggleButton ()
            self.widget.add (self.toggleLabel)
            self.widget.set_active (value)
            self.widget.connect ("toggled", self.activateSignal)
            self.widget.show()
        elif opt.type == "int" and opt.valid and len(opt.valid) == 1:
            adjustment = GtkAdjustment (value, opt.valid[0].start,
                                        opt.valid[0].end, 1, 10)
            self.widget = GtkSpinButton (adjustment, digits=0)
            adjustment.connect ("value_changed", self.activateSignal)
            self.widget.show()
        elif opt.type == "enum" or \
             (opt.valid and reduce (lambda x,y: x and y,
                                    map(lambda r: r.start==r.end, opt.valid))):
            self.widget = GtkCombo ()
            popdownStrings = []
            desc = opt.getDesc([lang])
            realValue = None
            self.comboEntries = {}
            for r in opt.valid:
                for v in range (r.start, r.end+1):
                    vString = dri.ValueToStr(v, opt.type)
                    if desc.enums.has_key(v):
                        string = desc.enums[v].encode(encoding)
                    else:
                        string = vString
                    self.comboEntries[string] = vString
                    popdownStrings.append (string)
                    if v == value:
                        realValue = string
            self.widget.set_popdown_strings (popdownStrings)
            self.widget.entry.set_text (realValue)
            self.widget.entry.set_editable (FALSE)
            self.widget.list.connect ("select_child", self.activateSignal)
            self.widget.show()
        else:
            self.widget = GtkEntry ()
            self.widget.set_text (dri.ValueToStr(value, opt.type))
            self.widget.connect ("activate", self.activateSignal)
            self.widget.show()
            self.invalidStyle = self.widget.get_style().copy()
            self.invalidStyle.fg[STATE_NORMAL] = \
                    self.widget.get_colormap().alloc(65535, 0, 0)

    def getValue (self):
        if self.widget.__class__ == GtkToggleButton:
            if self.widget.get_active():
                return "true"
            else:
                return "false"
        elif self.widget.__class__ == GtkSpinButton:
            return str(self.widget.get_value_as_int())
        elif self.widget.__class__ == GtkCombo:
            return self.comboEntries[self.widget.entry.get_text()]
        elif self.widget.__class__ == GtkEntry:
            return self.widget.get_text()
        else:
            return None

    def checkOpt (self, widget):
        if self.check.get_active():
            self.page.checkOpt (self.opt, self.getValue())
        else:
            self.page.checkOpt (self.opt, None)

    def activateSignal (self, widget, dummy=None):
        if self.widget.__class__ == GtkToggleButton:
            value = self.widget.get_active()
            if value:
                self.toggleLabel.set_text ("True")
            else:
                self.toggleLabel.set_text ("False")
        self.check.set_active (TRUE)
        self.checkOpt (widget)

    def validate (self):
        if not self.check.get_active():
            return 1
        valid = self.opt.validate (self.getValue())
        if not valid:
            if self.widget.__class__ == GtkEntry:
                self.widget.set_style (self.invalidStyle)
        else:
            if self.widget.__class__ == GtkEntry:
                self.widget.set_rc_style()
        return valid

class SectionPage (GtkScrolledWindow):
    def __init__ (self, optSection, app):
        GtkScrolledWindow.__init__ (self)
        self.set_policy (POLICY_AUTOMATIC, POLICY_AUTOMATIC)
        self.set_usize (400, 200)
        self.optSection = optSection
        self.app = app
        self.tooltips = GtkTooltips()
        self.table = GtkTable (len(optSection.optList), 2)
        self.optLines = []
        for i in range (len(optSection.optList)):
            self.optLines.append (OptionLine (self, i, optSection.optList[i]))
        self.table.show()
        self.add_with_viewport (self.table)

    def checkOpt (self, opt, value):
        if value != None and not self.app.options.has_key (opt.name):
            self.app.options[opt.name] = value
        elif value == None and self.app.options.has_key (opt.name):
            del self.app.options[opt.name]

    def commit (self):
        allValid = 1
        for optLine in self.optLines:
            valid = optLine.validate()
            if valid and self.app.options.has_key (optLine.opt.name):
                self.app.options[optLine.opt.name] = optLine.getValue()
            allValid = allValid and valid
        return allValid

class DriverPanel (GtkFrame):
    def __init__ (self, driver, app):
        GtkFrame.__init__ (self, "Application: " + app.name)
        self.driver = driver
        self.app = app
        table = GtkTable(2, 2)
        execLabel = GtkLabel ("Executable:")
        execLabel.show()
        table.attach (execLabel, 0, 1, 0, 1, 0, 0, 5, 5)
        self.execEntry = GtkEntry()
        if app.executable != None:
            self.execEntry.set_text (app.executable)
        self.execEntry.show()
        table.attach (self.execEntry, 1, 2, 0, 1, EXPAND|FILL, 0, 5, 5)
        notebook = GtkNotebook()
        self.sectPages = []
        self.sectLabels = []
        for sect in driver.optSections:
            sectPage = SectionPage (sect, app)
            sectPage.show()
            sectLabel = GtkLabel (sect.getDesc([lang]).encode(encoding))
            sectLabel.show()
            notebook.append_page (sectPage, sectLabel)
            self.sectPages.append (sectPage)
            self.sectLabels.append (sectLabel)
        if len(self.sectLabels) > 0:
            self.invalidStyle = self.sectLabels[0].get_style().copy()
            self.invalidStyle.fg[STATE_NORMAL] = \
                    self.sectLabels[0].get_colormap().alloc(65535, 0, 0)

        notebook.show()
        table.attach (notebook, 0, 2, 1, 2, FILL, EXPAND|FILL, 5, 5)
        table.show()
        self.add (table)

    def commit (self):
        executable = self.execEntry.get_text()
        if executable == "":
            self.app.executable = None
        else:
            self.app.executable = executable
        index = 0
        allValid = 1
        for sectPage in self.sectPages:
            valid = sectPage.commit()
            if not valid:
                self.sectLabels[index].set_style(self.invalidStyle)
            else:
                self.sectLabels[index].set_rc_style()
            allValid = allValid and valid
            index = index+1
        return allValid

    def renameApp (self):
        self.set_label ("Application: " + self.app.name)

class MessageDialog (GtkDialog):
    def __init__ (self, title, message, buttons = ["OK"], callback = None):
        GtkDialog.__init__ (self)
        self.callback = callback
        self.set_title (title)
        first = None
        for name in buttons:
            button = GtkButton (name)
            button.set_flags (CAN_DEFAULT)
            button.connect ("clicked", self.clickedSignal, name)
            button.show()
            self.action_area.pack_start (button, TRUE, FALSE, 10)
            if not first:
                first = button
        hbox = GtkHBox()
        label = GtkLabel (message)
        label.set_justify (JUSTIFY_LEFT)
        label.show()
        hbox.pack_start (label, TRUE, TRUE, 20)
        hbox.show()
        self.vbox.pack_start (hbox, TRUE, TRUE, 10)
        first.grab_default()
        self.set_modal (TRUE)
        self.show()

    def clickedSignal (self, widget, name):
        if self.callback:
            self.callback (name)
        self.destroy()

class BasicDialog (GtkDialog):
    def __init__ (self, title, callback):
        GtkDialog.__init__ (self)
        self.set_title (title)
        self.callback = callback
        ok = GtkButton ("OK")
        ok.set_flags (CAN_DEFAULT)
        ok.connect ("clicked", self.okSignal)
        ok.show()
        self.action_area.pack_start (ok, TRUE, FALSE, 10)
        cancel = GtkButton ("Cancel")
        cancel.set_flags (CAN_DEFAULT)
        cancel.connect ("clicked", self.cancelSignal)
        cancel.show()
        self.action_area.pack_start (cancel, TRUE, FALSE, 10)
        ok.grab_default()
        self.set_modal (TRUE)

    def okSignal (self, widget):
        self.callback()
        self.destroy()

    def cancelSignal (self, widget):
        self.destroy()

class NameDialog (BasicDialog):
    def __init__ (self, title, callback, name, data):
        BasicDialog.__init__ (self, title, callback)
        self.data = data
        hbox = GtkHBox()
        label = GtkLabel ("Name:")
        label.show()
        hbox.pack_start (label, TRUE, TRUE, 10)
        self.entry = GtkEntry()
        self.entry.set_text (name)
        self.entry.select_region (0, len(name))
        self.entry.connect ("activate", self.okSignal)
        self.entry.show()
        hbox.pack_start (self.entry, TRUE, TRUE, 10)
        hbox.show()
        self.vbox.pack_start (hbox, TRUE, TRUE, 10)
        self.show()
        self.entry.grab_focus()

    def okSignal (self, widget):
        self.callback (self.entry.get_text(), self.data)
        self.destroy()

class DeviceDialog (BasicDialog):
    def __init__ (self, title, callback, data):
        BasicDialog.__init__ (self, title, callback)
        self.data = data
        table = GtkTable (2, 2)
        screenLabel = GtkLabel ("Screen:")
        screenLabel.show()
        table.attach (screenLabel, 0, 1, 0, 1, 0, 0, 5, 5)
        self.screenCombo = GtkCombo()
        self.screenCombo.set_popdown_strings (
            [""]+map(str,range(len(dpy.screens))))
        self.screenCombo.entry.connect ("activate", self.screenSignal)
        self.screenCombo.list.connect ("select_child", self.screenSignal)
        self.screenCombo.show()
        table.attach (self.screenCombo, 1, 2, 0, 1, EXPAND|FILL, EXPAND, 5, 5)
        driverLabel = GtkLabel ("Driver:")
        driverLabel.show()
        table.attach (driverLabel, 0, 1, 1, 2, 0, 0, 5, 5)
        self.driverCombo = GtkCombo()
        self.driverCombo.set_popdown_strings (
            [""]+[str(driver.name) for driver in dri.DisplayInfo.drivers.values()])
        self.driverCombo.show()
        table.attach (self.driverCombo, 1, 2, 1, 2, EXPAND|FILL, EXPAND, 5, 5)
        table.show()
        self.vbox.pack_start (table, TRUE, TRUE, 5)
        self.show()

    def screenSignal (self, widget, data=None):
        screenName = self.screenCombo.entry.get_text()
        try:
            screenNum = int(screenName)
        except ValueError:
            pass
        else:
            screen = dpy.getScreen(screenNum)
            if screen != None:
                driver = screen.driver
                self.driverCombo.entry.set_text (str(driver.name))

    def okSignal (self, widget):
        self.callback (self.screenCombo.entry.get_text(),
                       self.driverCombo.entry.get_text(), self.data)
        self.destroy()

class ConfigTree (GtkCTree):
    def __init__ (self, configList):
        GtkCTree.__init__ (self, 1, 0)
        self.set_usize (200, 0)
        for config in configList:
            self.addConfig (config)
        self.connect ("select_row", self.selectRowSignal, None)

    def addConfig (self, config):
        fileName = str(config.fileName)
        fileNode = self.insert_node (None, None, [fileName], 0,
                                     None,None,None,None, FALSE, TRUE)
        config.node = fileNode
        self.node_set_row_data (fileNode, ("config", config))
        for device in config.devices:
            devNode = self.addDeviceNode (fileNode, device)
            for app in device.apps:
                self.addAppNode (devNode, app)

    def addDeviceNode (self, parent, device):
        if device.screen and device.driver:
            name = "Screen " + device.screen + " Driver " + device.driver
        elif device.screen:
            name = "Screen " + device.screen
        elif device.driver:
            name = "Driver " + device.driver
        else:
            name = "general"
        name = str(name)
        devNode = self.insert_node (parent, None, [name], 0,
                                    None,None,None,None, FALSE, TRUE)
        device.node = devNode
        self.node_set_row_data (devNode, ("device", device))
        return devNode

    def addAppNode (self, parent, app):
        name = str(app.name)
        appNode = self.insert_node (parent, None, [name])
        app.node = appNode
        self.node_set_row_data (appNode, ("app", app))
        return appNode

    def selectRowSignal (self, widget, row, column, event, data):
        type, obj = self.get_row_data (row)
        if type == "app":
            app = obj
            device = app.device
            driver = None
            if device.driver:
                driver = dri.GetDriver (device.driver)
            elif device.screen:
                try:
                    screenNum = int(device.screen)
                except ValueError:
                    pass
                else:
                    screen = dpy.getScreen(screenNum)
                    if screen != None:
                        driver = screen.driver
            if driver == None:
                MessageDialog ("Notice",
                               "Can't determine the driver for this device.")
        else:
            driver = None
            app = None
        if mainWindow.commitDriverPanel():
            mainWindow.switchDriverPanel (driver, app)
        else:
            self.select (mainWindow.curDriverPanel.app.node)

    def moveItem (self, inc):
        if len(self.selection) == 0:
            return
        if len(self.selection) > 1:
            print "multi selection!"
            return
        node = self.selection[0]
        type, obj = self.node_get_row_data (node)
        if type == "app":
            parent = obj.device
            siblings = parent.apps
        elif type == "device":
            parent = obj.config
            siblings = parent.devices
        else:
            return
        index = siblings.index (obj)
        newIndex = index+inc
        if newIndex < 0 or newIndex >= len(siblings):
            return
        siblings.remove (obj)
        siblings.insert (newIndex, obj)
        if newIndex == len(siblings)-1:
            siblingNode = None
        else:
            siblingNode = siblings[newIndex+1].node
        self.move (obj.node, parent.node, siblingNode)

    def moveUp (self, widget):
        self.moveItem (-1)

    def moveDown (self, widget):
        self.moveItem (1)

    def removeItem (self, widget):
        if len(self.selection) == 0:
            return
        if len(self.selection) > 1:
            print "multi selection!"
            return
        node = self.selection[0]
        type, obj = self.node_get_row_data (node)
        if type == "app":
            MessageDialog ("Question",
                           "Really delete application \"" + obj.name + "\"?",
                           ["Yes", "No"], self.doRemoveItem)
        elif type == "device":
            MessageDialog ("Question",
                           "Really delete device and all applications in it?",
                           ["Yes", "No"], self.doRemoveItem)
        else:
            MessageDialog ("Notice", "Select a device or application.")

    def doRemoveItem (self, buttonName):
        if buttonName != "Yes":
            return
        if len(self.selection) == 0:
            return
        if len(self.selection) > 1:
            print "multi selection!"
            return
        node = self.selection[0]
        type, obj = self.node_get_row_data (node)
        if type == "app":
            parent = obj.device
            siblings = parent.apps
        elif type == "device":
            parent = obj.config
            siblings = parent.devices
        else:
            return
        siblings.remove (obj)
        self.remove_node (node)
        if type == "app":
            mainWindow.removeApp (obj)
        elif type == "device":
            for app in obj.apps:
                mainWindow.removeApp (app)

    def renameApp (self, widget):
        if len(self.selection) == 0:
            return
        if len(self.selection) > 1:
            print "multi selection!"
            return
        node = self.selection[0]
        type, app = self.node_get_row_data (node)
        if type != "app":
            return
        dialog = NameDialog ("Rename Application", self.renameCallback,
                             app.name, app)

    def renameCallback (self, name, app):
        app.name = name
        self.node_set_text (app.node, 0, name)
        mainWindow.renameApp (app)

    def newItem (self, widget):
        if len(self.selection) == 0:
            MessageDialog ("Notice", "Select a configuration file or device.")
            return
        if len(self.selection) > 1:
            print "multi selection!"
            return
        node = self.selection[0]
        type, obj = self.node_get_row_data (node)
        if type == "device":
            dialog = NameDialog ("New Application", self.newAppCallback, "",
                                 obj)
        elif type == "config":
            dialog = DeviceDialog ("New Device", self.newDeviceCallback, obj)
        else:
            MessageDialog ("Notice", "Select a configuration file or device.")

    def newAppCallback (self, name, device):
        app = dri.AppConfig (device, name)
        device.apps.append (app)
        self.addAppNode (device.node, app)

    def newDeviceCallback (self, screen, driver, config):
        device = dri.DeviceConfig (config, screen, driver)
        config.devices.append (device)
        self.addDeviceNode (config.node, device)

    def saveConfig (self, widget):
        if len(self.selection) == 0:
            MessageDialog ("Notice", "Select a configuration file or device.")
            return
        if len(self.selection) > 1:
            print "multi selection!"
            return
        node = self.selection[0]
        type, config = self.node_get_row_data (node)
        if type != "config":
            MessageDialog ("Notice", "Select a configuration file.")
            return
        try:
            file = open (config.fileName, "w")
        except IOError:
            MessageDialog ("Error",
                           "Can't open \""+config.fileName+"\" for writing.")
            return
        valid = mainWindow.commitDriverPanel()
        file.write (str(config))
        file.close()
        if valid:
            MessageDialog ("Success",
                           "\""+config.fileName+"\" saved successfully.")
        else:
            MessageDialog ("Warning",
                           "\""+config.fileName+"\" saved with invalid entries.")

class MainWindow (GtkWindow):
    def __init__ (self, configList):
        GtkWindow.__init__ (self)
        self.set_title ("DRI Configuration")
        self.connect ("destroy", mainquit)
        self.connect ("delete_event", mainquit)
        self.vbox = GtkVBox()
        self.paned = GtkHPaned()
        self.configTree = ConfigTree (configList)
        self.configTree.show()
        self.paned.add1(self.configTree)
        self.paned.show()
        self.toolbar = GtkToolbar (ORIENTATION_HORIZONTAL, TOOLBAR_BOTH)
        self.toolbar.set_button_relief (RELIEF_NONE)
        self.toolbar.append_item ("Save", "Save selected configuration file", "priv",
                                  DataPixmap (self, tb_save_xpm),
                                  self.configTree.saveConfig)
        self.toolbar.append_item ("New", "Create a new device or application", "priv",
                                  DataPixmap (self, tb_new_xpm),
                                  self.configTree.newItem)
        self.toolbar.append_item ("Rename", "Rename selected application", "priv",
                                  DataPixmap (self, tb_edit_xpm),
                                  self.configTree.renameApp)
        self.toolbar.append_item ("Remove", "Remove selected device or application", "priv",
                                  DataPixmap (self, tb_trash_xpm),
                                  self.configTree.removeItem)
        self.toolbar.append_item ("Up", "Move selected item up", "priv",
                                  DataPixmap (self, tb_up_arrow_xpm),
                                  self.configTree.moveUp)
        self.toolbar.append_item ("Down", "Move selected item down", "priv",
                                  DataPixmap (self, tb_down_arrow_xpm),
                                  self.configTree.moveDown)
        self.toolbar.append_item ("Exit", "Exit DRI configuration", "priv",
                                  DataPixmap (self, tb_exit_xpm),
                                  mainquit)
        self.toolbar.show()
        self.vbox.pack_start (self.toolbar, FALSE, TRUE, 0)
        self.vbox.pack_start (self.paned, TRUE, TRUE, 0)
        self.vbox.show()
        self.add (self.vbox)
        self.curDriverPanel = None
        self.logo = DataPixmap (self, drilogo_xpm)
        self.logo.show()
        self.paned.add2 (self.logo)

    def commitDriverPanel (self):
        if self.curDriverPanel != None:
            return self.curDriverPanel.commit()
        else:
            return 1

    def switchDriverPanel (self, driver=None, app=None):
        if self.curDriverPanel != None:
            if self.curDriverPanel.driver == driver and \
               self.curDriverPanel.app == app:
                return
            self.paned.remove (self.curDriverPanel)
        elif driver != None:
            self.paned.remove (self.logo)
        if driver != None:
            self.curDriverPanel = DriverPanel (driver, app)
            self.curDriverPanel.show ()
            self.paned.add2 (self.curDriverPanel)
        elif self.curDriverPanel != None:
            self.curDriverPanel = None
            self.logo.show()
            self.paned.add2 (self.logo)

    def removeApp (self, app):
        if self.curDriverPanel != None and self.curDriverPanel.app == app:
            self.paned.remove (self.curDriverPanel)
            self.curDriverPanel = None
            self.logo.show()
            self.paned.add2 (self.logo)

    def renameApp (self, app):
        if self.curDriverPanel != None and self.curDriverPanel.app == app:
            self.curDriverPanel.renameApp()

def main():
    # initialize locale
    global lang, encoding
    locale.setlocale(locale.LC_ALL, '')
    lang,encoding = locale.getlocale()
    if lang:
        underscore = lang.find ('_')
        if underscore != -1:
            lang = lang[0:underscore]
    else:
        lang = "en"
    if not encoding:
        encoding = "ISO-8859-1"

    # read configuration information from the drivers
    global dpy
    dpy = dri.DisplayInfo ()

    # open the main window
    global mainWindow
    mainWindow = MainWindow([])
    mainWindow.show ()

    # read configuration files
    fileNameList = ["/etc/drirc", os.environ["HOME"] + "/.drirc"]
    configList = []
    for fileName in fileNameList:
        try:
            cfile = open (fileName, "r")
        except IOError:
            config = dri.DRIConfig (None, fileName)
            for screen in dpy.screens:
                if screen == None:
                    continue
                device = dri.DeviceConfig (config, str(screen.num),
                                           screen.driver.name)
                app = dri.AppConfig (device, "all")
                device.apps.append (app)
                config.devices.append (device)
        else:
            try:
                config = dri.DRIConfig (cfile)
            except dri.XMLError, problem:
                MessageDialog ("Error", "Configuration file \""+fileName+\
                               "\" contains errors: "+str(problem)+"\n"+\
                               "I will leave the file alone until you fix the problem manually or remove the file.")
                continue
        mainWindow.configTree.addConfig (config)

    # run
    mainloop()
