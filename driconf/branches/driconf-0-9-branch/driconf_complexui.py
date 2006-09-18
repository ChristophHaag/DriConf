# DRI configuration GUI: complex UI components

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

import dri
import pygtk
pygtk.require ("2.0")
import gtk
import gobject

import driconf_commonui
commonui = driconf_commonui    # short cut

from driconf_commonui import _, lang, findInShared, escapeMarkup, WrappingCheckButton, SectionPage, UnknownSectionPage

class DriverPanel (gtk.Frame):
    """ Panel for driver settings for a specific application. """
    def __init__ (self, driver, app):
        """ Constructor. """
        gtk.Frame.__init__ (self)
        frameLabel = gtk.Label()
        frameLabel.set_markup ("<b>" + escapeMarkup(
            _("Application")+": "+app.name) + "</b>")
        frameLabel.show()
        self.set_label_widget (frameLabel)
        self.driver = driver
        self.app = app
        tooltips = gtk.Tooltips()
        table = gtk.Table(2, 2)
        self.execCheck = WrappingCheckButton (_("Apply only to this executable"))
        self.execCheck.set_sensitive (app.device.config.writable)
        tooltips.set_tip (self.execCheck, _(
            "Leave this disabled to configure all applications.\n"
            "Beware that some applications or games are just a shell script "
            "that starts a real executable with a different name."))
        self.execCheck.show()
        table.attach (self.execCheck, 0, 1, 0, 1, 0, 0, 5, 5)
        self.execEntry = gtk.Entry()
        if app.executable != None:
            self.execCheck.set_active (True)
            self.execEntry.set_text (app.executable)
        self.execEntry.set_sensitive (app.device.config.writable and
                                      app.executable != None)
        self.execEntry.show()
        self.execCheck.connect ("toggled", self.execToggled)
        self.execEntry.connect ("changed", self.execChanged)
        table.attach (self.execEntry, 1, 2, 0, 1,
                      gtk.EXPAND|gtk.FILL, 0, 5, 5)
        notebook = gtk.Notebook()
        notebook.popup_enable()
        notebook.set_scrollable (True)
        self.sectPages = []
        self.sectLabels = []
        unknownPage = UnknownSectionPage (driver, app)
        if not driver or len(unknownPage.opts) > 0:
            unknownPage.show()
            unknownLabel = gtk.Label (_("Unknown"))
            unknownLabel.show()
            notebook.append_page (unknownPage, unknownLabel)
            self.sectPages.append (unknownPage)
            self.sectLabels.append (unknownLabel)
        if driver:
            for sect in driver.optSections:
                sectPage = SectionPage (sect, app, False)
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
        self.validate()
        notebook.show()
        table.attach (notebook, 0, 2, 1, 2,
                      gtk.FILL, gtk.EXPAND|gtk.FILL, 5, 5)
        table.show()
        self.add (table)

    def execChanged (self, widget):
        self.app.modified(self.app)

    def execToggled (self, widget):
        self.execEntry.set_sensitive (self.execCheck.get_active())
        self.app.modified(self.app)

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
                self.sectLabels[index].modify_fg (
                    gtk.STATE_NORMAL, self.default_normal_fg)
                self.sectLabels[index].modify_fg (
                    gtk.STATE_ACTIVE, self.default_active_fg)
            allValid = allValid and valid
            index = index+1
        return allValid

    def commit (self):
        """ Commit changes to the configuration. """
        executable = self.execEntry.get_text()
        if not self.execCheck.get_active():
            if self.app.executable != None:
                self.app.executable = None
                self.app.modified(self.app)
        elif executable != self.app.executable:
            self.app.executable = executable
            self.app.modified(self.app)
        for sectPage in self.sectPages:
            sectPage.commit()

    def renameApp (self):
        """ Change the application name. """
        self.set_label ("Application: " + self.app.name)

class NameDialog (gtk.Dialog):
    """ Dialog for setting the name of an application. """
    def __init__ (self, title, callback, name, data):
        gtk.Dialog.__init__ (self, title, commonui.mainWindow,
                             gtk.DIALOG_DESTROY_WITH_PARENT|gtk.DIALOG_MODAL,
                             (gtk.STOCK_OK, gtk.RESPONSE_OK,
                              gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.callback = callback
        self.data = data
        self.connect ("response", self.responseSignal)
        table = gtk.Table(2, 2)
        commentLabel = gtk.Label (_(
            "Enter the name of the application below. This just serves as "
            "a description for you. Don't forget to set the executable "
            "afterwards."))
        commentLabel.set_line_wrap (True)
        commentLabel.show()
        table.attach (commentLabel, 0, 2, 0, 1,
                      gtk.EXPAND|gtk.FILL, gtk.EXPAND, 10, 5)
        label = gtk.Label (_("Application Name"))
        label.show()
        table.attach (label, 0, 1, 1, 2, 0, gtk.EXPAND, 10, 5)
        self.entry = gtk.Entry()
        self.entry.set_text (name)
        self.entry.select_region (0, len(name))
        self.entry.connect ("activate", self.activateSignal)
        self.entry.show()
        table.attach (self.entry, 1, 2, 1, 2,
                      gtk.EXPAND|gtk.FILL, gtk.EXPAND, 10, 5)
        table.show()
        self.vbox.pack_start (table, True, True, 5)
        self.show()
        self.entry.grab_focus()

    def activateSignal (self, widget):
        self.response (gtk.RESPONSE_OK)

    def responseSignal (self, dialog, response):
        if response == gtk.RESPONSE_OK:
            self.callback (self.entry.get_text(), self.data)
        self.destroy()

class DeviceDialog (gtk.Dialog):
    """ Dialog for choosing driver and screen of a device. """
    def __init__ (self, title, callback, data):
        gtk.Dialog.__init__ (self, title, commonui.mainWindow,
                             gtk.DIALOG_DESTROY_WITH_PARENT|gtk.DIALOG_MODAL,
                             (gtk.STOCK_OK, gtk.RESPONSE_OK,
                              gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.callback = callback
        self.data = data
        self.connect ("response", self.responseSignal)
        table = gtk.Table (2, 3)
        commentLabel = gtk.Label (_(
            "Describe the device that you would like to configure."))
        commentLabel.set_line_wrap (True)
        commentLabel.show()
        table.attach (commentLabel, 0, 2, 0, 1,
                      gtk.EXPAND|gtk.FILL, gtk.EXPAND, 10, 5)
        screenLabel = gtk.Label (_("Screen Number"))
        screenLabel.show()
        table.attach (screenLabel, 0, 1, 1, 2, 0, gtk.EXPAND, 10, 5)
        self.screenCombo = gtk.Combo()
        self.screenCombo.set_popdown_strings (
            [""]+map(str,range(len(commonui.dpy.screens))))
        self.screenCombo.entry.connect ("activate", self.screenSignal)
        self.screenCombo.list.connect ("select_child", self.screenSignal)
        self.screenCombo.show()
        table.attach (self.screenCombo, 1, 2, 1, 2,
                      gtk.EXPAND|gtk.FILL, gtk.EXPAND, 10, 5)
        driverLabel = gtk.Label (_("Driver Name"))
        driverLabel.show()
        table.attach (driverLabel, 0, 1, 2, 3, 0, gtk.EXPAND, 10, 5)
        self.driverCombo = gtk.Combo()
        self.driverCombo.set_popdown_strings (
            [""]+[str(driver.name) for driver in dri.DisplayInfo.drivers.values()])
        self.driverCombo.show()
        table.attach (self.driverCombo, 1, 2, 2, 3,
                      gtk.EXPAND|gtk.FILL, gtk.EXPAND, 10, 5)
        if data and data.__class__ == dri.DeviceConfig:
            if data.screen:
                self.screenCombo.entry.set_text (data.screen)
            if data.driver:
                self.driverCombo.entry.set_text (data.driver)
        table.show()
        self.vbox.pack_start (table, True, True, 5)
        self.show()

    def screenSignal (self, widget, data=None):
        screenName = self.screenCombo.entry.get_text()
        try:
            screenNum = int(screenName)
        except ValueError:
            pass
        else:
            screen = commonui.dpy.getScreen(screenNum)
            if screen != None:
                driver = screen.driver
                self.driverCombo.entry.set_text (str(driver.name))

    def responseSignal (self, dialog, response):
        if response == gtk.RESPONSE_OK:
            self.callback (self.screenCombo.entry.get_text(),
                           self.driverCombo.entry.get_text(), self.data)
        self.destroy()

class ConfigTreeModel (gtk.GenericTreeModel):
    # constructur
    def __init__ (self, configList):
        gtk.GenericTreeModel.__init__ (self)
        self.configList = []
        for config in configList:
            self.addNode (config)

    def iconFromShared (self, name, size, missing):
        path = findInShared (name)
        if path:
            icon = gtk.gdk.pixbuf_new_from_file (path)
            return icon.scale_simple (size, size, gtk.gdk.INTERP_BILINEAR)
        else:
            return missing

    def renderIcons (self, widget):
        self.configIcon = widget.render_icon ("gtk-properties",
                                              gtk.ICON_SIZE_MENU, None)
        self.appIcon = widget.render_icon ("gtk-execute",
                                           gtk.ICON_SIZE_MENU, None)
        self.unspecIcon = widget.render_icon ("gtk-dialog-question",
                                              gtk.ICON_SIZE_MENU, None)
        missing = widget.render_icon ("gtk-missing-image",
                                      gtk.ICON_SIZE_MENU, None)
        size = max (missing.get_width(), missing.get_height())
        self.screenIcon = self.iconFromShared ("screen.png", size, missing)
        self.driverIcon = self.iconFromShared ("card.png", size, missing)
        self.screenDriverIcon = self.iconFromShared ("screencard.png",
                                                     size, missing)

    # implementation of the GenericTreeModel interface
    def on_get_flags (self):
        return gtk.TREE_MODEL_ITERS_PERSIST
    def on_get_n_columns (self):
        return 2
    def on_get_column_type (self, col):
        if col == 0:
            return gobject.TYPE_OBJECT
        else:
            return gobject.TYPE_STRING
    def on_get_path (self, node):
        if node.__class__ == dri.DRIConfig:
            return (self.configList.index(node),)
        elif node.__class__ == dri.DeviceConfig:
            config = node.config
            return (self.configList.index(config),
                    config.devices.index(node))
        elif node.__class__ == dri.AppConfig:
            device = node.device
            config = device.config
            return (self.configList.index(config),
                    config.devices.index(device),
                    device.apps.index(node))
        else:
            assert 0
    def on_get_iter (self, path):
        if len(path) > 3:
            return None
        configIndex = path[0] # config
        if configIndex < len(self.configList):
            config = self.configList[configIndex]
        else:
            return None
        if len(path) == 1:
            return config
        deviceIndex = path[1] # device
        if deviceIndex < len(config.devices):
            device = config.devices[deviceIndex]
        else:
            return None
        if len(path) == 2:
            return device
        appIndex = path[2] # application
        if appIndex < len(device.apps):
            app = device.apps[appIndex]
        else:
            return None
        return app
    def on_get_value (self, node, col):
        if node.__class__ == dri.DRIConfig:
            if col == 0:
                return self.configIcon
            else:
                return "<b>" + escapeMarkup(str(node.fileName)) + "</b>"
        elif node.__class__ == dri.DeviceConfig:
            if node.screen and node.driver:
                name = _("%s on screen %s") % (node.driver.capitalize(),
                                               node.screen)
                icon = self.screenDriverIcon
            elif node.screen:
                name = _("Screen %s") % node.screen
                icon = self.screenIcon
            elif node.driver:
                name = "%s" % node.driver.capitalize()
                icon = self.driverIcon
            else:
                name = _("Unspecified device")
                icon = self.unspecIcon
            if col == 0:
                return icon
            else:
                return escapeMarkup(str(name))
        elif node.__class__ == dri.AppConfig:
            if col == 0:
                return self.appIcon
            elif not node.isValid:
                return '<span foreground="red">' + \
                       escapeMarkup(str(node.name)) + '</span>'
            else:
                return escapeMarkup(str(node.name))
    def on_iter_next (self, node):
        if node.__class__ == dri.DRIConfig:
            list = self.configList
        elif node.__class__ == dri.DeviceConfig:
            list = node.config.devices
        elif node.__class__ == dri.AppConfig:
            list = node.device.apps
        else:
            return None
        index = list.index(node)
        if index+1 < len(list):
            return list[index+1]
        else:
            return None
    def on_iter_children (self, node):
        return self.on_iter_nth_child (node, 0)
    def on_iter_has_child (self, node):
        return (self.on_iter_n_children (node) > 0)
    def on_iter_n_children (self, node):
        if not node:
            return len(self.configList)
        elif node.__class__ == dri.DRIConfig:
            return len(node.devices)
        elif node.__class__ == dri.DeviceConfig:
            return len(node.apps)
        else:
            return 0
    def on_iter_nth_child (self, node, index):
        if not node:
            list = self.configList
        elif node.__class__ == dri.DRIConfig:
            list = node.devices
        elif node.__class__ == dri.DeviceConfig:
            list = node.apps
        else:
            return None
        if len(list) > index:
            return list[index]
        else:
            return None
    def on_iter_parent (self, node):
        if node.__class__ == dri.DeviceConfig:
            return node.config
        elif node.__class__ == dri.AppConfig:
            return node.device
        else:
            return None

    # helpers for converting between nodes, paths and TreeIterators
    def getPathFromNode (self, node):
        return self.on_get_path (node)
    def getNodeFromPath (self, path):
        return self.on_get_iter (path)
    def getIterFromNode (self, node):
        return self.get_iter (self.getPathFromNode(node))

    # config list
    def getConfigList (self):
        return self.configList

    # callback for registring modifications
    def nodeModified (self, node, b=True):
        if node.__class__ == dri.DRIConfig:
            config = node
        elif node.__class__ == dri.DeviceConfig:
            config = node.config
        elif node.__class__ == dri.AppConfig:
            config = node.device.config
        if config.isModified != b:
            config.isModified = b
            curNode = commonui.mainWindow.configTree.getSelection (allowNone=True)
            if not curNode:
                commonui.mainWindow.deactivateButtons()
            elif curNode.__class__ == dri.DRIConfig:
                commonui.mainWindow.activateConfigButtons(curNode)
            elif curNode.__class__ == dri.DeviceConfig:
                commonui.mainWindow.activateDeviceButtons(curNode)
            elif curNode.__class__ == dri.AppConfig:
                commonui.mainWindow.activateAppButtons(curNode)

    # higher level model manipulations
    def addNode (self, node, sibling = None):
        """ Add a new node and inform the TreeView. """
        self.initNode (node)
        if node.__class__ == dri.DRIConfig:
            list = self.configList
        elif node.__class__ == dri.DeviceConfig:
            list = node.config.devices
        elif node.__class__ == dri.AppConfig:
            list = node.device.apps
        if sibling != None:
            index = list.index (sibling)
            list.insert (index, node)
        else:
            list.append (node)
        self.registerNode (node)
    def initNode (self, node):
        node.modified = self.nodeModified
        if node.__class__ == dri.DRIConfig:
            if not hasattr(node,"isModified"):
                node.isModified = False
            for device in node.devices:
                self.initNode (device)
        elif node.__class__ == dri.DeviceConfig:
            for app in node.apps:
                self.initNode (app)
        elif node.__class__ == dri.AppConfig:
            self.validateAppNode (node)
    def registerNode (self, node):
        path = self.on_get_path (node)
        iter = self.get_iter (path)
        self.row_inserted (path, iter)
        if node.__class__ == dri.DRIConfig:
            for device in node.devices:
                self.registerNode (device)
        elif node.__class__ == dri.DeviceConfig:
            for app in node.apps:
                self.registerNode (app)
    def removeNode (self, node):
        if node.__class__ == dri.DRIConfig:
            list = self.configList
            while len(node.devices) > 0:
                self.removeNode (node.devices[0])
        elif node.__class__ == dri.DeviceConfig:
            list = node.config.devices
            while len(node.apps) > 0:
                self.removeNode (node.apps[0])
        elif node.__class__ == dri.AppConfig:
            list = node.device.apps
        path = self.on_get_path (node)
        list.remove (node)
        self.row_deleted (path)

    # find the first writable application
    def findFirstWritableApp (self):
        foundApp = None
        for config in self.configList:
            if not config.writable:
                continue
            for device in config.devices:
                if len(device.apps) > 0:
                    foundApp = device.apps[0]
                    break
        return foundApp

    # validate an application node
    def validateAppNode (self, app):
        try:
            driver = app.device.getDriver(commonui.dpy)
        except dri.XMLError:
            driver = None
        if driver and not driver.validate (app.options):
            app.isValid = False
        else:
            app.isValid = True

class ConfigTreeView (gtk.TreeView):
    def __init__ (self, configList):
        self.model = ConfigTreeModel (configList)
        gtk.TreeView.__init__ (self, self.model)
        self.model.renderIcons (self)
        self.connect ("style-set", lambda widget, prevStyle:
                      self.model.renderIcons (widget))
        self.set_size_request (200, -1)
        self.set_headers_visible (False)
        self.expand_all()
        self.get_selection().set_mode (gtk.SELECTION_BROWSE)
        self.get_selection().connect ("changed", self.selectionChangedSignal)
        column = gtk.TreeViewColumn()
        column.set_spacing (2)
        renderPixbuf = gtk.CellRendererPixbuf()
        column.pack_start (renderPixbuf, expand=False)
        column.add_attribute (renderPixbuf, "pixbuf", 0)
        renderText = gtk.CellRendererText()
        column.pack_start (renderText, expand=True)
        column.add_attribute (renderText, "markup", 1)
        self.append_column (column)

    def getConfigList (self):
        return self.model.getConfigList()

    # selection handling
    def getSelection (self, allowNone=False):
        model, iter = self.get_selection().get_selected()
        assert iter or allowNone
        if iter:
            path = self.model.get_path (iter)
            return self.model.getNodeFromPath (path)
        else:
            return None
    def selectFirstWritableApp (self):
        app = self.model.findFirstWritableApp()
        if app:
            path = self.model.getPathFromNode (app)
            self.get_selection().select_path (path)
            self.scroll_to_cell (path=path, use_align=False)
    def selectionChangedSignal (self, data):
        node = self.getSelection (allowNone=True)
        if not node:
            driver = None
            app = None
        elif node.__class__ == dri.AppConfig:
            app = node
            try:
                driver = app.device.getDriver (commonui.dpy)
            except dri.XMLError, problem:
                driver = None
                dialog = gtk.MessageDialog (
                    commonui.mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                    _("Parsing the driver's configuration information: %s") %
                    problem)
                dialog.connect ("response", lambda d,r: d.destroy())
                dialog.show()
        else:
            driver = None
            app = None
        commonui.mainWindow.commitDriverPanel()
        commonui.mainWindow.switchDriverPanel (driver, app)
        if not node:
            commonui.mainWindow.deactivateButtons()
        elif node.__class__ == dri.DRIConfig:
            commonui.mainWindow.activateConfigButtons(node)
        elif node.__class__ == dri.DeviceConfig:
            commonui.mainWindow.activateDeviceButtons(node)
        elif node.__class__ == dri.AppConfig:
            commonui.mainWindow.activateAppButtons(node)

    # highlight invalid nodes
    def validateAppNode (self, app):
        self.model.validateAppNode (app)
        # Emit a row_changed event so that the view gets updated properly.
        path = self.model.getPathFromNode (app)
        iter = self.model.get_iter (path)
        self.model.row_changed (path, iter)

    # UI actions on the config tree
    def moveUp (self, widget):
        self.moveItem (-1)
    def moveDown (self, widget):
        self.moveItem (1)
    def removeItem (self, widget):
        node = self.getSelection()
        if node.__class__ == dri.AppConfig:
            parent = node.device
            dialog = gtk.MessageDialog (
                commonui.mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                _("Really delete application \"%s\"?") % node.name)
        elif node.__class__ == dri.DeviceConfig:
            parent = node.config
            dialog = gtk.MessageDialog (
                commonui.mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                _("Really delete device and all applications in it?"))
        else:
            # The remove button should be unsensitive.
            assert False
        response = dialog.run()
        dialog.destroy ()
        if response != gtk.RESPONSE_YES:
            return
        if node.__class__ == dri.AppConfig:
            commonui.mainWindow.removeApp (node)
        elif node.__class__ == dri.DeviceConfig:
            for app in node.apps:
                commonui.mainWindow.removeApp (app)
        self.model.removeNode (node)
        parent.modified(parent)
        path = self.model.getPathFromNode (parent)
        self.get_selection().select_path (path)
        self.scroll_to_cell (path=path, use_align=False)
    def properties (self, widget):
        node = self.getSelection()
        if node.__class__ == dri.AppConfig:
            dialog = NameDialog (_("Rename Application"),
                                 self.renameCallback, node.name, node)
        else:
            dialog = DeviceDialog (_("Device Properties"),
                                   self.propertiesCallback, node)
    def newItem (self, widget):
        node = self.getSelection()
        if node.__class__ == dri.AppConfig:
            node = node.device
        if node.__class__ == dri.DeviceConfig:
            dialog = NameDialog (_("New Application"), self.newAppCallback, "",
                                 node)
        elif node.__class__ == dri.DRIConfig:
            dialog = DeviceDialog (_("New Device"), self.newDeviceCallback,
                                   node)
    def saveConfig (self, widget):
        node = self.getSelection()
        if node.__class__ == dri.AppConfig:
            config = node.device.config
        elif node.__class__ == dri.DeviceConfig:
            config = node.config
        elif node.__class__ == dri.DRIConfig:
            config = node
        valid = True
        for device in config.devices:
            try:
                driver = device.getDriver (commonui.dpy)
            except dri.XMLError:
                driver = None
            if driver == None:
                continue
            for app in device.apps:
                valid = valid and driver.validate (app.options)
        if not valid:
            dialog = gtk.MessageDialog (
                commonui.mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                _("The configuration contains invalid entries. Save anyway?"))
            response = dialog.run()
            dialog.destroy()
            if response != gtk.RESPONSE_YES:
                return
        try:
            file = open (config.fileName, "w")
        except IOError:
            dialog = gtk.MessageDialog (
                commonui.mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                _("Can't open \"%s\" for writing.") % config.fileName)
            dialog.run()
            dialog.destroy()
            return
        commonui.mainWindow.commitDriverPanel()
        file.write (str(config))
        file.close()
        config.modified(config, False)
    def reloadConfig (self, widget):
        node = self.getSelection()
        if node.__class__ == dri.AppConfig:
            config = node.device.config
        elif node.__class__ == dri.DeviceConfig:
            config = node.config
        else:
            config = node
        dialog = gtk.MessageDialog (
            commonui.mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
            _("Really reload \"%s\" from disk?") % config.fileName)
        response = dialog.run()
        dialog.destroy()
        if response != gtk.RESPONSE_YES:
            return
        try:
            cfile = open (config.fileName, "r")
        except IOError:
            dialog = gtk.MessageDialog (
                commonui.mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                _("Couldn't open \"%s\" for reading. "
                  "The file was not reloaded.") % config.fileName)
            dialog.run()
            dialog.destroy()
            return
        # Try to parse the configuration file.
        try:
            newConfig = dri.DRIConfig (cfile)
        except dri.XMLError, problem:
            dialog = gtk.MessageDialog (
                commonui.mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                _("Configuration file \"%s\" contains errors:\n"
                  "%s\n"
                  "The file was not reloaded.") %
                (config.fileName, str(problem)))
            dialog.run()
            dialog.destroy()
            cfile.close()
            return
        cfile.close()
        # Check if the file is writable in the end.
        newConfig.writable = commonui.fileIsWritable (config.fileName)
        # find the position of config
        configList = self.getConfigList()
        index = configList.index (config)
        if index == len(configList)-1:
            sibling = None
        else:
            sibling = configList[index+1]
        if node.__class__ == dri.AppConfig:
            commonui.mainWindow.removeApp (node)
        elif node.__class__ == dri.DeviceConfig:
            for app in node.apps:
                commonui.mainWindow.removeApp (app)
        self.model.removeNode (config)
        self.model.addNode (newConfig, sibling)
        path = self.model.getPathFromNode (newConfig)
        self.expand_row (path, True)
        self.get_selection().select_path (path)
        self.scroll_to_cell (path=path, use_align=False)

    # helper function for moving tree nodes around
    def moveItem (self, inc):
        node = self.getSelection()
        if node.__class__ == dri.AppConfig:
            parent = node.device
            siblings = parent.apps
        elif node.__class__ == dri.DeviceConfig:
            parent = node.config
            siblings = parent.devices
        else:
            assert False
        index = siblings.index (node)
        newIndex = index+inc
        if newIndex < 0 or newIndex >= len(siblings):
            return
        siblings.remove (node)
        siblings.insert (newIndex, node)
        newOrder = range(len(siblings))
        newOrder[index] = newIndex
        newOrder[newIndex] = index
        path = self.model.getPathFromNode (parent)
        iter = self.model.get_iter (path)
        self.model.rows_reordered (path, iter, newOrder)
        parent.modified(parent)
        path = self.model.getPathFromNode (node)
        self.scroll_to_cell (path=path, use_align=False)

    # callbacks from dialogs
    def renameCallback (self, name, app):
        app.name = name
        path = self.model.getPathFromNode (app)
        iter = self.model.get_iter (path)
        self.model.row_changed (path, iter)
        commonui.mainWindow.renameApp (app)
        app.modified(app)
    def propertiesCallback (self, screen, driver, device):
        device.screen = screen
        device.driver = driver
        path = self.model.getPathFromNode (device)
        iter = self.model.get_iter (path)
        self.model.row_changed (path, iter)
        device.modified(device)
    def newAppCallback (self, name, device):
        app = dri.AppConfig (device, name)
        self.model.addNode (app)
        if len(device.apps) == 1:
            self.expand_row (self.model.getPathFromNode(device), True)
        device.modified(device)
        path = self.model.getPathFromNode (app)
        self.get_selection().select_path (path)
        self.scroll_to_cell (path=path, use_align=False)
    def newDeviceCallback (self, screen, driver, config):
        device = dri.DeviceConfig (config, screen, driver)
        self.model.addNode (device)
        config.modified(config)
        path = self.model.getPathFromNode (device)
        self.get_selection().select_path (path)
        self.scroll_to_cell (path=path, use_align=False)

class MainWindow (gtk.Window):
    """ The main window consiting of ConfigTree, DriverPanel and toolbar. """
    def __init__ (self, configList):
        gtk.Window.__init__ (self)
        self.set_title ("DRIconf")
        self.connect ("destroy", lambda dummy: gtk.main_quit())
        self.connect ("delete_event", self.exitHandler)
        self.vbox = gtk.VBox()
        self.paned = gtk.HPaned()
        self.configTree = ConfigTreeView (configList)
        self.configTree.show()
        scrolledWindow = gtk.ScrolledWindow ()
        scrolledWindow.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolledWindow.add (self.configTree)
        scrolledWindow.show()
        self.paned.add1(scrolledWindow)
        self.paned.show()
        self.toolbar = gtk.Toolbar ()
        iconSize = self.toolbar.get_icon_size()
        self.saveButton = self.toolbar.insert_stock (
            "gtk-save", _("Save selected configuration file"),
            "priv", self.configTree.saveConfig, None, -1)
        self.reloadButton = self.toolbar.insert_stock (
            "gtk-revert-to-saved", _("Reload selected configuration file"),
            "priv", self.configTree.reloadConfig, None, -1)
        self.toolbar.append_space()
        self.newButton = self.toolbar.insert_stock (
            "gtk-new", _("Create a new device or application"),
            "priv", self.configTree.newItem, None, -1)
        self.removeButton = self.toolbar.insert_stock (
            "gtk-delete", _("Remove selected device or application"),
            "priv", self.configTree.removeItem, None, -1)
        self.upButton = self.toolbar.insert_stock (
            "gtk-go-up", _("Move selected item up"),
            "priv", self.configTree.moveUp, None, -1)
        self.downButton = self.toolbar.insert_stock (
            "gtk-go-down", _("Move selected item down"),
            "priv", self.configTree.moveDown, None, -1)
        self.propertiesButton = self.toolbar.insert_stock (
            "gtk-properties", _("Properties of selected device or application"),
            "priv", self.configTree.properties, None, -1)
        self.toolbar.append_space()
        # The gtk-about stock item is available with gtk >= 2.6.
        # It's definitely not available with gtk 2.2. Not sure about 2.4.
        if gtk.gtk_version[0] == 2 and gtk.gtk_version[1] < 6:
            aboutStock = "gtk-dialog-info"
        else:
            aboutStock = "gtk-about"
        self.aboutButton = self.toolbar.insert_stock (
            aboutStock, _("About DRIconf"), "priv",
            self.aboutHandler, None, -1)
        self.toolbar.append_space()
        self.exitButton = self.toolbar.insert_stock (
            "gtk-quit", _("Exit DRIconf"), "priv",
            self.exitHandler, None, -1)
        if len(configList) != 0:
            self.activateConfigButtons (configList[0])
        self.toolbar.show()
        self.vbox.pack_start (self.toolbar, False, True, 0)
        self.vbox.pack_start (self.paned, True, True, 0)
        self.vbox.show()
        self.add (self.vbox)
        self.curDriverPanel = None
        self.logo = gtk.EventBox ()
        logoPath = findInShared("drilogo.jpg")
        if logoPath:
            image = gtk.Image()
            image.set_from_file (logoPath)
            self.logo.add (image)
        self.logo.modify_bg (gtk.STATE_NORMAL,
                             gtk.gdk.Color (65535, 65535, 65535))
        self.logo.show_all()
        self.paned.add2 (self.logo)

    def initSelection (self):
        self.configTree.selectFirstWritableApp()

    def commitDriverPanel (self):
        if self.curDriverPanel != None:
            self.curDriverPanel.commit()
            self.configTree.validateAppNode (self.curDriverPanel.app)

    def validateDriverPanel (self):
        if self.curDriverPanel != None:
            self.curDriverPanel.validate()
            self.curDriverPanel.commit()
            self.configTree.validateAppNode (self.curDriverPanel.app)

    def switchDriverPanel (self, driver=None, app=None):
        if self.curDriverPanel != None:
            if self.curDriverPanel.driver == driver and \
               self.curDriverPanel.app == app:
                return
            self.paned.remove (self.curDriverPanel)
        elif app != None:
            self.paned.remove (self.logo)
        if app != None:
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

    def deactivateButtons (self):
        self.saveButton      .set_sensitive (False)
        self.reloadButton    .set_sensitive (False)
        self.newButton       .set_sensitive (False)
        self.removeButton    .set_sensitive (False)
        self.upButton        .set_sensitive (False)
        self.downButton      .set_sensitive (False)
        self.propertiesButton.set_sensitive (False)

    def activateConfigButtons (self, config):
        writable = config.writable
        modified = config.isModified
        self.saveButton      .set_sensitive (writable and modified)
        self.reloadButton    .set_sensitive (True)
        self.newButton       .set_sensitive (writable)
        self.removeButton    .set_sensitive (False)
        self.upButton        .set_sensitive (False)
        self.downButton      .set_sensitive (False)
        self.propertiesButton.set_sensitive (False)

    def activateDeviceButtons (self, device):
        writable = device.config.writable
        modified = device.config.isModified
        self.saveButton      .set_sensitive (writable and modified)
        self.reloadButton    .set_sensitive (True)
        self.newButton       .set_sensitive (writable)
        self.removeButton    .set_sensitive (writable)
        self.upButton        .set_sensitive (writable)
        self.downButton      .set_sensitive (writable)
        self.propertiesButton.set_sensitive (writable)

    def activateAppButtons (self, app):
        # Button sensitivity is identical for apps and devices.
        self.activateDeviceButtons (app.device)

    def aboutHandler (self, widget):
        dialog = commonui.AboutDialog()
        dialog.connect("response",
                       lambda dialog, response: dialog.destroy())
        dialog.show()

    def exitHandler (self, widget, event=None):
        modified = False
        for config in self.configTree.getConfigList():
            if config.isModified:
                modified = True
                break
        if modified:
            dialog = gtk.MessageDialog (
                commonui.mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT|gtk.DIALOG_MODAL,
                gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                _("There are unsaved modifications. Exit anyway?"))
            dialog.connect ("response", self.doExit)
            dialog.show()
            return True
        elif event == None:
            # called from toolbar button: main_quit!
            gtk.main_quit()
        else:
            # called from delete_event: indicate it's ok to destroy
            return False

    def doExit (self, dialog, response):
        dialog.destroy()
        if response == gtk.RESPONSE_YES:
            gtk.main_quit()

def start (configList):
    # initSelection must be called before and after mainWindow.show().
    # Before makes sure that the initial window size is correct.
    # After is needed since the selection seems to get lost in
    # mainWindow.show().
    mainWindow = MainWindow(configList)
    commonui.mainWindow = mainWindow
    mainWindow.set_default_size (750, 375)
    mainWindow.initSelection()
    mainWindow.show ()
    mainWindow.initSelection()
