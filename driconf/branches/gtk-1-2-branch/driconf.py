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
try:
    import pygtk
    # make sure gtk version 1.2 is used.
    pygtk.require ("1.2")
except ImportError:
    # not supported everywhere, so ignore import errors
    pass
from gtk import *
from driconf_xpm import *

# global variable: main window
mainWindow = None

class DataPixmap (GtkPixmap):
    """ A pixmap made from data. """
    window = None
    def __init__ (self, data):
        """ Constructor. """
        DataPixmap.window.realize()
        style = DataPixmap.window.get_style()
        pixmap, mask = create_pixmap_from_xpm_d(DataPixmap.window.get_window(),
                                                style.bg[STATE_NORMAL],
                                                data)
        GtkPixmap.__init__ (self, pixmap, mask)

class MessageDialog (GtkDialog):
    """ A simple message dialog with configurable buttons and a callback. """
    def __init__ (self, title, message, buttons = ["OK"], callback = None,
                  modal = TRUE):
        """ Constructor. """
        GtkDialog.__init__ (self)
        if mainWindow:
            self.set_transient_for (mainWindow)
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
        label.set_line_wrap (TRUE)
        label.show()
        hbox.pack_start (label, TRUE, TRUE, 20)
        hbox.show()
        self.vbox.pack_start (hbox, TRUE, TRUE, 10)
        first.grab_default()
        self.set_modal (modal)
        self.show()

    def clickedSignal (self, widget, name):
        """ Handler for clicked signals. """
        if self.callback:
            self.callback (name)
        self.destroy()

class WrappingCheckButton (GtkCheckButton):
    """ Check button with a line wrapping label. """
    def __init__ (self, label, justify=JUSTIFY_LEFT, wrap=TRUE,
                  width=0, height=0):
        """ Constructor. """
        GtkCheckButton.__init__ (self)
        checkHBox = GtkHBox()
        checkLabel = GtkLabel(label)
        checkLabel.set_justify (justify)
        checkLabel.set_line_wrap (wrap)
        checkLabel.set_usize (width, height)
        checkLabel.show()
        checkHBox.pack_start (checkLabel, FALSE, FALSE, 0)
        checkHBox.show()
        self.add (checkHBox)

class WrappingOptionMenu (GtkButton):
    """ Something that looks similar to a GtkOptionMenu ...

    but can wrap the text and has a simpler interface. It acts as a
    bidirectional map from option descriptions (opt) to values (val)
    at the same time. """
    def __init__ (self, optValList, callback, justify=JUSTIFY_LEFT, wrap=TRUE,
                  width=0, height=0):
        """ Constructor. """
        GtkButton.__init__ (self)
        self.callback = callback
        self.optDict = {}
        self.valDict = {}
        for opt,val in optValList:
            self.optDict[opt] = val
            self.valDict[val] = opt
        firstOpt,firstVal = optValList[len(optValList)-1]
        self.value = firstVal
        hbox = GtkHBox()
        arrow = GtkArrow (ARROW_DOWN, SHADOW_OUT)
        arrow.show()
        self.label = GtkLabel(firstOpt)
        self.label.set_justify (justify)
        self.label.set_line_wrap (wrap)
        self.label.set_usize (width, height)
        self.label.show()
        hbox.pack_start (self.label, TRUE, FALSE, 5)
        hbox.pack_start (arrow, FALSE, FALSE, 0)
        hbox.show()
        self.add (hbox)
        self.menu = GtkMenu()
        for opt,val in optValList:
            item = GtkMenuItem (opt)
            item.connect("activate", self.menuSelect, opt)
            item.show()
            self.menu.append (item)
        self.connect("event", self.buttonPress)

    def setOpt (self, opt):
        """ Select an option by the option description. """
        self.label.set_text (opt)
        self.value = self.optDict[opt]

    def setValue (self, value):
        """ Select an option by its value. """
        self.label.set_text (self.valDict[value])
        self.value = value

    def getValue (self):
        """ Return the current value. """
        return self.value

    def buttonPress (self, widget, event):
        """ Popup the menu. """
        if event.type == GDK.BUTTON_PRESS:
            self.menu.popup(None, None, None, event.button, event.time)
            return TRUE
        else:
            return FALSE

    def menuSelect (self, widget, opt):
        """ React to selection of a menu item by the user. """
        self.setOpt (opt)
        self.callback (self)

class OptionLine:
    """ One line in a SectionPage. """
    def __init__ (self, page, i, opt):
        """ Constructor. """
        self.page = page
        self.opt = opt
        typeString = opt.type
        if opt.valid:
            typeString = typeString+" ["+ \
                         reduce(lambda x,y: x+','+y, map(str,opt.valid))+"]"
        # a check button with an option description
        desc = opt.getDesc([lang])
        if desc != None:
            desc = desc.text
        else:
            desc = u"(no description available)"
        self.check = WrappingCheckButton (desc.encode(encoding), width=200)
        self.check.set_active (page.app.options.has_key (opt.name))
        self.check.set_sensitive (page.app.device.config.writable)
        self.check.connect ("clicked", self.checkOpt)
        tooltipString = str(opt)
        page.tooltips.set_tip (self.check, tooltipString.encode(encoding))
        self.check.show()
        page.table.attach (self.check, 0, 1, i, i+1, EXPAND|FILL, 0, 5, 5)
        # a button to reset the option to its default value
        sensitive = self.check.get_active() and page.app.device.config.writable
        self.resetButton = GtkButton ()
        pixmap = DataPixmap (tb_undo_xpm)
        pixmap.show()
        self.resetButton.add (pixmap)
        self.resetButton.set_relief (RELIEF_NONE)
        self.resetButton.set_sensitive (sensitive)
        self.resetButton.connect ("clicked", self.resetOpt)
        self.resetButton.show()
        page.table.attach (self.resetButton, 2, 3, i, i+1, 0, 0, 5, 5)

        # get the option value, if it's invalid leave it as a string
        if page.app.options.has_key (opt.name):
            self.isValid = opt.validate (page.app.options[opt.name])
            try:
                value = dri.StrToValue (page.app.options[opt.name], opt.type)
            except dri.XMLError:
                self.isValid = FALSE
            if not self.isValid:
                value = page.app.options[opt.name]
        else:
            value = opt.default
            self.isValid = TRUE
        # the widget for editing the option value
        self.initWidget (opt, value)
        self.widget.set_sensitive (sensitive)
        page.table.attach (self.widget, 1, 2, i, i+1, FILL, 0, 5, 5)

    def initWidget (self, opt, value):
        """ Initialize the option widget.

        The widget type is selected automatically based in the option type
        and the set/range of valid values. """
        type = opt.type
        if not self.isValid:
            type = "invalid"
        if type == "bool":
            self.toggleLabel = GtkLabel()
            if value:
                self.toggleLabel.set_text ("Yes")
            else:
                self.toggleLabel.set_text ("No")
            self.toggleLabel.show()
            self.widget = GtkToggleButton ()
            self.widget.add (self.toggleLabel)
            self.widget.set_active (value)
            self.widget.connect ("toggled", self.activateSignal)
        elif type == "int" and opt.valid and len(opt.valid) == 1:
            adjustment = GtkAdjustment (value, opt.valid[0].start,
                                        opt.valid[0].end, 1, 10)
            self.widget = GtkSpinButton (adjustment, digits=0)
            self.widget.set_value (value)
            adjustment.connect ("value_changed", self.activateSignal)
        elif type == "enum" or \
             (type != "invalid" and opt.valid and
              reduce (lambda x,y: x and y, map(dri.Range.empty, opt.valid))):
            desc = opt.getDesc([lang])
            optValList = []
            for r in opt.valid:
                if type == "enum":
                    for v in range (r.start, r.end+1):
                        vString = dri.ValueToStr(v, type)
                        if type == "enum" and desc and desc.enums.has_key(v):
                            string = desc.enums[v].encode(encoding)
                        else:
                            string = vString
                        optValList.append ((string, vString))
                else:
                    vString = dri.ValueToStr(r.start, type)
                    optValList.append ((vString, vString))
            self.widget = WrappingOptionMenu (optValList, self.activateSignal,
                                              width=180)
            self.widget.setValue(str(value))
        else:
            self.widget = GtkEntry ()
            if type == "invalid":
                self.widget.set_text (value)
            else:
                self.widget.set_text (dri.ValueToStr(value, type))
            self.widget.connect ("changed", self.activateSignal)
        self.highlightInvalid()
        self.widget.show()

    def updateWidget (self, value, valid):
        """ Update the option widget to a new value. """
        if self.widget.__class__ == GtkToggleButton:
            self.widget.set_active (value)
        elif self.widget.__class__ == GtkSpinButton:
            self.widget.set_value (value)
        elif self.widget.__class__ == WrappingOptionMenu:
            self.widget.setValue(str(value))
        elif self.widget.__class__ == GtkEntry:
            if self.opt.type == "bool" and valid:
                if value:
                    newText = "true"
                else:
                    newText = "false"
            else:
                newText = str(value)
            # only set new text if it changed, otherwise the changed signal
            # is triggered without a real value change
            if newText != self.widget.get_text():
                self.widget.set_text (newText)

    def getValue (self):
        """ Get the current value from the option widget.

        Returns None if the widget is not activated. """
        if not self.check.get_active():
            return None
        elif self.widget.__class__ == GtkToggleButton:
            if self.widget.get_active():
                return "true"
            else:
                return "false"
        elif self.widget.__class__ == GtkSpinButton:
            return str(self.widget.get_value_as_int())
        elif self.widget.__class__ == WrappingOptionMenu:
            return self.widget.getValue()
        elif self.widget.__class__ == GtkEntry:
            return self.widget.get_text()
        else:
            return None

    def checkOpt (self, widget):
        """ Handler for 'check button (maybe) toggled'. """
        if self.check.get_active():
            self.widget.set_sensitive (TRUE)
            self.resetButton.set_sensitive (TRUE)
        else:
            self.widget.set_sensitive (FALSE)
            self.resetButton.set_sensitive (FALSE)
        self.page.optionModified (self)

    def activateSignal (self, widget, dummy=None):
        """ Handler for 'widget was activated by the user'. """
        if self.widget.__class__ == GtkToggleButton:
            value = self.widget.get_active()
            if value:
                self.toggleLabel.set_text ("Yes")
            else:
                self.toggleLabel.set_text ("No")
        self.doValidate()
        self.page.optionModified (self)

    def resetOpt (self, widget):
        """ Reset to default value. """
        self.updateWidget (self.opt.default, TRUE)
        self.page.optionModified (self)

    def doValidate (self):
        """ Validate the current value from the option widget.

        This is only interesting if the check button is active. Only
        GtkEntry widgets should ever give invalid values in practice.
        Invalid option widgets are highlighted. If the validity changed
        then have the page check if its validity was changed, too. """
        value = self.getValue()
        if value == None:
            return
        valid = self.opt.validate (value)
        if (valid and not self.isValid) or (not valid and self.isValid):
            self.isValid = valid
            self.highlightInvalid()
            self.page.doValidate()

    def highlightInvalid (self):
        if not self.isValid:
            if self.widget.__class__ == GtkEntry:
                style = self.widget.get_style().copy()
                style.fg[STATE_NORMAL] = self.widget.get_colormap().alloc(65535, 0, 0)
                self.widget.set_style (style)
        else:
            if self.widget.__class__ == GtkEntry:
                self.widget.set_rc_style()

    def validate (self):
        return self.isValid

class SectionPage (GtkScrolledWindow):
    """ One page in the DriverPanel with one OptionLine per option. """
    def __init__ (self, optSection, app):
        """ Constructor. """
        GtkScrolledWindow.__init__ (self)
        self.set_policy (POLICY_AUTOMATIC, POLICY_AUTOMATIC)
        self.set_usize (500, 200)
        self.optSection = optSection
        self.app = app
        self.tooltips = GtkTooltips()
        self.table = GtkTable (len(optSection.optList), 3)
        self.optLines = []
        for i in range (len(optSection.optList)):
            self.optLines.append (OptionLine (self, i, optSection.optList[i]))
        self.table.show()
        self.add_with_viewport (self.table)
        self.doValidate (init=TRUE)

    def optionModified (self, optLine):
        """ Callback that is invoked by changed option lines. """
        self.app.device.config.modifiedCallback()

    def doValidate (self, init=FALSE):
        """ Validate the widget settings.

        The return value indicates if there are invalid option values. """
        valid = TRUE
        for optLine in self.optLines:
            if not optLine.validate():
                valid = FALSE
                break
        if not init and \
               ((valid and not self.isValid) or (not valid and self.isValid)):
            self.isValid = valid
            mainWindow.validateDriverPanel()
        self.isValid = valid

    def validate (self):
        return self.isValid

    def commit (self):
        """ Commit the widget settings. """
        for optLine in self.optLines:
            name = optLine.opt.name
            value = optLine.getValue()
            if value == None and self.app.options.has_key(name):
                del self.app.options[name]
                self.app.device.config.modifiedCallback()
            elif value != None:
                if not self.app.options.has_key(name) or \
                   (self.app.options.has_key(name) and \
                    value != self.app.options[name]):
                    self.app.device.config.modifiedCallback()
                self.app.options[name] = value

class UnknownSectionPage(GtkVBox):
    """ Special section page for options unknown to the driver. """
    def __init__ (self, driver, app):
        """ Constructor. """
        GtkVBox.__init__ (self)
        scrolledWindow = GtkScrolledWindow ()
        scrolledWindow.set_policy (POLICY_AUTOMATIC, POLICY_AUTOMATIC)
        self.app = app
        # copy options (dict function does not exist in Python 2.1 :( )
        self.opts = {}
        for name,val in app.options.items():
            self.opts[name] = val
        # remove all options known to the driver
        for sect in driver.optSections:
            for opt in sect.optList:
                if self.opts.has_key (opt.name):
                    del self.opts[opt.name]
        # short cut
        if len(self.opts) == 0:
            return
        # list all remaining options here
        self.list = GtkCList(2, ["Option", "Value"])
        self.list.set_selection_mode (SELECTION_EXTENDED)
        for name,val in self.opts.items():
            self.list.append ([str(name),str(val)])
        self.list.set_column_justification (1, JUSTIFY_RIGHT)
        self.list.columns_autosize()
        self.list.show()
        scrolledWindow.add (self.list)
        scrolledWindow.show()
        self.pack_start (scrolledWindow, TRUE, TRUE, 0)
        self.removeButton = GtkButton ("Remove")
        self.removeButton.show()
        self.removeButton.connect ("clicked", self.removeSelection)
        self.pack_start (self.removeButton, FALSE, FALSE, 0)

    def validate (self):
        """ These options can't be validated. """
        return TRUE

    def commit (self):
        """ These options are never changed. """
        pass

    def removeSelection (self, widget):
        """ Remove the selected items from the list and app config. """
        # must delete from back to front. make a copy of selection and sort it
        selection = self.list.selection[:]
        selection.sort()
        selection.reverse()
        for row in selection:
            name = self.list.get_text (row, 0)
            del self.app.options[name]
            self.list.remove (row)
            self.app.device.config.modifiedCallback()

class DriverPanel (GtkFrame):
    """ Panel for driver settings for a specific application. """
    def __init__ (self, driver, app):
        """ Constructor. """
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
        self.execEntry.set_sensitive (app.device.config.writable)
        self.execEntry.connect ("changed", self.execChanged)
        self.execEntry.show()
        table.attach (self.execEntry, 1, 2, 0, 1, EXPAND|FILL, 0, 5, 5)
        notebook = GtkNotebook()
        self.sectPages = []
        self.sectLabels = []
        for sect in driver.optSections:
            sectPage = SectionPage (sect, app)
            sectPage.show()
            desc = sect.getDesc([lang])
            if desc:
                sectLabel = GtkLabel (desc.encode(encoding))
            else:
                sectLabel = GtkLabel ("(no description)")
            sectLabel.show()
            notebook.append_page (sectPage, sectLabel)
            self.sectPages.append (sectPage)
            self.sectLabels.append (sectLabel)
        unknownPage = UnknownSectionPage (driver, app)
        if len(unknownPage.opts) > 0:
            unknownPage.show()
            unknownLabel = GtkLabel ("Unknown")
            unknownLabel.show()
            notebook.append_page (unknownPage, unknownLabel)
            self.sectPages.append (unknownPage)
            self.sectLabels.append (unknownLabel)
            MessageDialog ("Notice",
                           "This application configuration contains options that are not known to the driver. Either you edited your configuration file manually or the driver configuration changed. See the page named \"Unknown\" for details. It is probably safe to remove these options. Otherwise they are left unchanged.", modal=FALSE)
        self.validate()
        notebook.show()
        table.attach (notebook, 0, 2, 1, 2, FILL, EXPAND|FILL, 5, 5)
        table.show()
        self.add (table)

    def execChanged (self, widget):
        self.app.device.config.modifiedCallback()

    def validate (self):
        """ Validate the configuration.

        Labels of invalid section pages are highlighted. Returns whether
        there were invalid option values. """
        index = 0
        allValid = TRUE
        for sectPage in self.sectPages:
            valid = sectPage.validate()
            if not valid:
                style = self.sectLabels[index].get_style().copy()
                style.fg[STATE_NORMAL] = self.sectLabels[index].get_colormap().alloc(65535, 0, 0)
                self.sectLabels[index].set_style(style)
            else:
                self.sectLabels[index].set_rc_style()
            allValid = allValid and valid
            index = index+1
        return allValid

    def commit (self):
        """ Commit changes to the configuration. """
        executable = self.execEntry.get_text()
        if executable == "":
            if self.app.executable != None:
                self.app.executable = None
                self.app.device.config.modifiedCallback()
        elif executable != self.app.executable:
            self.app.executable = executable
            self.app.device.config.modifiedCallback()
        for sectPage in self.sectPages:
            sectPage.commit()

    def renameApp (self):
        """ Change the application name. """
        self.set_label ("Application: " + self.app.name)

class BasicDialog (GtkDialog):
    """ Base class for NameDialog and DeviceDialog. """
    def __init__ (self, title, callback):
        GtkDialog.__init__ (self)
        self.set_transient_for (mainWindow)
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
    """ Dialog for setting the name of an application. """
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
    """ Dialog for choosing driver and screen of a device. """
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
    """ Configuration tree.

    Hierarchy levels: Config (file), Device, Application """
    class SelectionError (Exception):
        """ Something's wrong with the selection. """
        pass
    
    def __init__ (self, configList):
        GtkCTree.__init__ (self, 1, 0)
        self.set_usize (200, 0)
        self.set_column_auto_resize (0, TRUE)
        self.set_selection_mode (SELECTION_BROWSE)
        self.defaultFg = self.get_style().fg[STATE_NORMAL]
        self.configList = []
        for config in configList:
            self.addConfig (config)
        self.connect ("select_row", self.selectRowSignal, None)

    def getConfigList (self):
        return self.configList

    def addConfig (self, config, sibling=None):
        if sibling != None:
            index = self.configList.index (sibling)
            self.configList.insert (index, config)
            siblingNode = sibling.node
        else:
            self.configList.append (config)
            siblingNode = None
        fileName = str(config.fileName)
        fileNode = self.insert_node (None, siblingNode, [fileName], 0,
                                     None,None,None,None, FALSE, TRUE)
        config.modified = FALSE
        config.modifiedCallback = self.configModified
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
        self.validateAppNode(app)
        return appNode

    def validateAppNode (self, app):
        try:
            driver = app.device.getDriver(dpy)
        except dri.XMLError:
            driver = None
        if driver:
            if driver.validate (app.options):
                style = self.get_style().copy()
                style.fg[STATE_NORMAL] = self.defaultFg
                style.fg[STATE_SELECTED] = self.defaultFg
                self.node_set_row_style(app.node, style)
            else:
                style = self.get_style().copy()
                style.fg[STATE_NORMAL] = self.get_colormap().alloc(65535, 0, 0)
                style.fg[STATE_SELECTED] = self.get_colormap().alloc(65535, 0, 0)
                self.node_set_row_style(app.node, style)

    def selectFirstWritableApp (self):
        foundApp = None
        for config in self.configList:
            if len(config.devices) > 0 and len(config.devices[0].apps) > 0:
                foundApp = config.devices[0].apps[0]
                if config.writable:
                    break
        self.select (foundApp.node)
        return foundApp

    def getSelection (self):
        if len(self.selection) == 0:
            raise SelectionError
        if len(self.selection) > 1:
            print "multi selection!"
            raise SelectionError
        return self.selection[0]

    def configModified (self, b=TRUE):
        try:
            node = self.getSelection()
        except SelectionError:
            return
        type, obj = self.node_get_row_data (node)
        if type == "config":
            config = obj
        elif type == "device":
            config = obj.config
        elif type == "app":
            config = obj.device.config
        if config.modified != b:
            config.modified = b
            if type == "config":
                mainWindow.activateConfigButtons(obj)
            elif type == "device":
                mainWindow.activateDeviceButtons(obj)
            elif type == "app":
                mainWindow.activateAppButtons(obj)

    def selectRowSignal (self, widget, row, column, event, data):
        type, obj = self.get_row_data (row)
        self.selectTypeObj (type, obj)

    def selectTypeObj (self, type, obj):
        if type == "app":
            app = obj
            try:
                driver = app.device.getDriver (dpy)
            except dri.XMLError, problem:
                driver = None
                MessageDialog ("Error",
                               "Parsing the driver's configuration information: " + str(problem),
                               modal=FALSE)
            else:
                if driver == None:
                    MessageDialog ("Notice",
                                   "Can't determine the driver for this device.",
                                   modal=FALSE)
        else:
            driver = None
            app = None
        mainWindow.commitDriverPanel()
        mainWindow.switchDriverPanel (driver, app)
        if type == "config":
            mainWindow.activateConfigButtons(obj)
        elif type == "device":
            mainWindow.activateDeviceButtons(obj)
        elif type == "app":
            mainWindow.activateAppButtons(obj)

    def moveItem (self, inc):
        try:
            node = self.getSelection()
        except SelectionError:
            return
        type, obj = self.node_get_row_data (node)
        if type == "app":
            parent = obj.device
            config = parent.config
            siblings = parent.apps
        elif type == "device":
            parent = obj.config
            config = parent
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
        config.modifiedCallback()

    def moveUp (self, widget):
        self.moveItem (-1)

    def moveDown (self, widget):
        self.moveItem (1)

    def removeItem (self, widget):
        try:
            node = self.getSelection()
        except SelectionError:
            return
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
        try:
            node = self.getSelection()
        except SelectionError:
            return
        type, obj = self.node_get_row_data (node)
        if type == "app":
            parent = obj.device
            config = parent.config
            siblings = parent.apps
        elif type == "device":
            parent = obj.config
            config = parent
            siblings = parent.devices
        else:
            return
        siblings.remove (obj)
        if type == "app":
            mainWindow.removeApp (obj)
        elif type == "device":
            for app in obj.apps:
                mainWindow.removeApp (app)
        self.remove_node (node)
        config.modifiedCallback()

    def renameApp (self, widget):
        try:
            node = self.getSelection()
        except SelectionError:
            return
        type, app = self.node_get_row_data (node)
        if type != "app":
            return
        dialog = NameDialog ("Rename Application", self.renameCallback,
                             app.name, app)

    def renameCallback (self, name, app):
        app.name = name
        self.node_set_text (app.node, 0, name)
        mainWindow.renameApp (app)
        app.device.config.modifiedCallback()

    def newItem (self, widget):
        try:
            node = self.getSelection()
        except SelectionError:
            return
        type, obj = self.node_get_row_data (node)
        if type == "app":
            obj = obj.device
            type = "device"
        if type == "device":
            dialog = NameDialog ("New Application", self.newAppCallback, "",
                                 obj)
        elif type == "config":
            dialog = DeviceDialog ("New Device", self.newDeviceCallback, obj)

    def newAppCallback (self, name, device):
        app = dri.AppConfig (device, name)
        device.apps.append (app)
        self.addAppNode (device.node, app)
        app.device.config.modifiedCallback()

    def newDeviceCallback (self, screen, driver, config):
        device = dri.DeviceConfig (config, screen, driver)
        config.devices.append (device)
        self.addDeviceNode (config.node, device)
        device.config.modifiedCallback()

    def saveConfig (self, widget):
        self.doSaveConfig()

    def doSaveConfig (self, reallySave="dunno"):
        if reallySave == "No":
            return
        try:
            node = self.getSelection()
        except SelectionError:
            return
        type, config = self.node_get_row_data (node)
        if type == "app":
            config = config.device
            type = "device"
        if type == "device":
            config = config.config
            type = "config"
        if reallySave == "dunno":
            valid = 1
            for device in config.devices:
                try:
                    driver = device.getDriver (dpy)
                except dri.XMLError:
                    driver = None
                if driver == None:
                    continue
                for app in device.apps:
                    valid = valid and driver.validate (app.options)
            if not valid:
                MessageDialog ("Question",
                               "The configuration contains invalid entries. Save anyway?",
                               ["Yes", "No"], self.doSaveConfig)
                return
        try:
            file = open (config.fileName, "w")
        except IOError:
            MessageDialog ("Error",
                           "Can't open \""+config.fileName+"\" for writing.")
            return
        mainWindow.commitDriverPanel()
        file.write (str(config))
        file.close()
        config.modifiedCallback(FALSE)

    def reloadConfig (self, widget):
        self.doReloadConfig ()

    def doReloadConfig (self, reallyReload="dunno"):
        if reallyReload == "No":
            return
        try:
            node = self.getSelection()
        except SelectionError:
            return
        type, obj = self.node_get_row_data (node)
        if type == "app":
            config = obj.device.config
        elif type == "device":
            config = obj.config
        else:
            config = obj
        if reallyReload == "dunno":
            MessageDialog ("Question",
                           "Really reload " + config.fileName + " from disk?",
                           ["Yes", "No"], self.doReloadConfig)
            return
        try:
            cfile = open (config.fileName, "r")
        except IOError:
            MessageDialog ("Notice",
                           "Couldn't open " + config.fileName + " for reading. The file was not reloaded.")
            return
        # Try to parse the configuration file.
        try:
            newConfig = dri.DRIConfig (cfile)
        except dri.XMLError, problem:
            MessageDialog ("Error", "Configuration file \""+config.fileName+
                           "\" contains errors:\n"+str(problem)+
                           "\nThe file was not reloaded.")
            cfile.close()
            return
        cfile.close()
        # Check if the file is writable in the end.
        newConfig.writable = fileIsWritable (config.fileName)
        # find the position of config
        index = self.configList.index (config)
        if index == len(self.configList)-1:
            sibling = None
        else:
            sibling = self.configList[index+1]
        self.configList.remove (config)
        if type == "app":
            mainWindow.removeApp (obj)
        elif type == "device":
            for app in obj.apps:
                mainWindow.removeApp (app)
        self.remove_node (config.node)
        self.addConfig (newConfig, sibling)

class MainWindow (GtkWindow):
    """ The main window consiting of ConfigTree, DriverPanel and toolbar. """
    def __init__ (self, configList):
        GtkWindow.__init__ (self)
        self.set_title ("DRI Configuration")
        self.connect ("destroy", mainquit)
        self.connect ("delete_event", self.exitHandler)
        self.vbox = GtkVBox()
        self.paned = GtkHPaned()
        self.configTree = ConfigTree (configList)
        self.configTree.show()
        scrolledWindow = GtkScrolledWindow ()
        scrolledWindow.set_policy (POLICY_AUTOMATIC, POLICY_AUTOMATIC)
        scrolledWindow.add (self.configTree)
        scrolledWindow.show()
        self.paned.add1(scrolledWindow)
        self.paned.show()
        DataPixmap.window = self
        self.toolbar = GtkToolbar (ORIENTATION_HORIZONTAL, TOOLBAR_BOTH)
        self.toolbar.set_button_relief (RELIEF_NONE)
        self.toolbar.set_space_style (TOOLBAR_SPACE_LINE)
        self.saveButton = self.toolbar.append_item (
            "Save", "Save selected configuration file", "priv",
            DataPixmap (tb_save_xpm), self.configTree.saveConfig)
        self.reloadButton = self.toolbar.append_item (
            "Reload", "Reload selected configuration file", "priv",
            DataPixmap (tb_revert_xpm), self.configTree.reloadConfig)
        self.toolbar.append_space()
        self.newButton = self.toolbar.append_item (
            "New", "Create a new device or application", "priv",
            DataPixmap (tb_new_xpm), self.configTree.newItem)
        self.removeButton = self.toolbar.append_item (
            "Remove", "Remove selected device or application", "priv",
            DataPixmap (tb_trash_xpm), self.configTree.removeItem)
        self.upButton = self.toolbar.append_item (
            "Up", "Move selected item up", "priv",
            DataPixmap (tb_up_arrow_xpm), self.configTree.moveUp)
        self.downButton = self.toolbar.append_item (
            "Down", "Move selected item down", "priv",
            DataPixmap (tb_down_arrow_xpm), self.configTree.moveDown)
        self.renameButton = self.toolbar.append_item (
            "Rename", "Rename selected application", "priv",
            DataPixmap (tb_edit_xpm), self.configTree.renameApp)
        self.toolbar.append_space()
        self.exitButton = self.toolbar.append_item (
            "Exit", "Exit DRI configuration", "priv",
            DataPixmap (tb_exit_xpm), self.exitHandler)
        if len(configList) != 0:
            self.activateConfigButtons (configList[0])
        self.toolbar.show()
        self.vbox.pack_start (self.toolbar, FALSE, TRUE, 0)
        self.vbox.pack_start (self.paned, TRUE, TRUE, 0)
        self.vbox.show()
        self.add (self.vbox)
        self.curDriverPanel = None
        self.logo = GtkEventBox()
        self.logo.add (DataPixmap (drilogo_xpm))
        style = self.logo.get_style().copy()
        style.bg[STATE_NORMAL] = self.get_colormap().alloc(65535, 65535, 65535)
        self.logo.set_style (style)
        self.logo.show_all()
        self.paned.add2 (self.logo)

    def initSelection (self):
        app = self.configTree.selectFirstWritableApp()
        # initSelection is called before the mainloop runs, so there is no
        # selection signal. We have to "emit" it manually.
        self.configTree.selectTypeObj ("app", app)

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

    def activateConfigButtons (self, config):
        writable = config.writable
        modified = config.modified
        self.saveButton  .set_sensitive (writable and modified)
        self.newButton   .set_sensitive (writable)
        self.removeButton.set_sensitive (FALSE)
        self.upButton    .set_sensitive (FALSE)
        self.downButton  .set_sensitive (FALSE)
        self.renameButton.set_sensitive (FALSE)

    def activateDeviceButtons (self, device):
        writable = device.config.writable
        modified = device.config.modified
        self.saveButton  .set_sensitive (writable and modified)
        self.newButton   .set_sensitive (writable)
        self.removeButton.set_sensitive (writable)
        self.upButton    .set_sensitive (writable)
        self.downButton  .set_sensitive (writable)
        self.renameButton.set_sensitive (FALSE)

    def activateAppButtons (self, app):
        writable = app.device.config.writable
        modified = app.device.config.modified
        self.saveButton  .set_sensitive (writable and modified)
        self.newButton   .set_sensitive (writable)
        self.removeButton.set_sensitive (writable)
        self.upButton    .set_sensitive (writable)
        self.downButton  .set_sensitive (writable)
        self.renameButton.set_sensitive (writable)

    def exitHandler (self, widget, event=None):
        modified = FALSE
        for config in self.configTree.getConfigList():
            if config.modified:
                modified = TRUE
                break
        if modified:
            MessageDialog ("Question",
                           "There are unsaved modifications. Exit anyway?",
                           ["Yes", "No"], self.doExit)
            return TRUE
        elif event == None:
            mainquit()
        else:
            return FALSE

    def doExit (self, choice):
        if choice == "Yes":
            mainquit()

def fileIsWritable(filename):
    """ Find out if a file is writable.

    Returns 1 for existing writable files, 0 otherwise. """
    try:
        fd = os.open (filename, os.O_WRONLY)
    except OSError:
        return 0
    if fd == -1:
        return 0
    else:
        os.close (fd)
        return 1

def main():
    # initialize locale
    global lang, encoding
    locale.setlocale(locale.LC_ALL, '')
    lang,encoding = locale.getlocale(locale.LC_MESSAGES)
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
    try:
        dpy = dri.DisplayInfo ()
    except dri.DRIError, problem:
        MessageDialog ("Error", str(problem), callback = lambda n: mainquit())
        mainloop()
        return
    except dri.XMLError, problem:
        MessageDialog ("Error",
                       "There are errors in a driver's configuration information:\n"+
                       str(problem)+
                       "\nThis should not happen. It probably means that you have to update driconf.",
                       callback = lambda n: mainquit())
        mainloop()
        return

    # read or create configuration files
    fileNameList = ["/etc/drirc", os.environ["HOME"] + "/.drirc"]
    configList = []
    newFiles = []
    for fileName in fileNameList:
        try:
            cfile = open (fileName, "r")
        except IOError:
            # Make a default configuration file.
            config = dri.DRIConfig (None, fileName)
            config.writable = 1
            for screen in dpy.screens:
                if screen == None:
                    continue
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
            except dri.XMLError, problem:
                MessageDialog ("Error", "Configuration file \""+fileName+
                               "\" contains errors:\n"+str(problem)+
                               "\nI will leave the file alone until you fix the problem manually or remove the file.",
                               callback = lambda n: mainquit())
                mainloop()
                continue
            else:
                # Check if the file is writable in the end.
                config.writable = fileIsWritable (fileName)
            cfile.close()
        if config:
            configList.append (config)

    # open the main window
    global mainWindow
    mainWindow = MainWindow(configList)
    mainWindow.initSelection()
    mainWindow.show ()

    if len(newFiles) == 1:
        MessageDialog ("Notice", "Created a new DRI configuration file " +
                       newFiles[0] + " for you.")
    elif len(newFiles) > 1:
        MessageDialog ("Notice", "Created new configuration files " +
                       reduce(lambda a, b: str(a) + " and " + str(b), newFiles)
                       + " for you.")

    # run
    mainloop()
