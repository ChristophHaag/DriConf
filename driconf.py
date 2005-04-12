# DRI configuration GUI using python-gtk

# Copyright (C) 2003-2005  Felix Kuehling

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
import math
import gettext
import dri
import pygtk
pygtk.require ("2.0")
import gtk
import gobject

# Install translations. Search in the current directory first (for
# easy testing). Then search in the default location and in
# /usr/local/share/locale. If all this fails fall back to the null
# translation.
try:
    _ = gettext.translation ("driconf", ".").ugettext
except IOError:
    try:
        _ = gettext.translation ("driconf").ugettext
    except IOError:
        _ = gettext.translation ("driconf", "/usr/local/share/locale",
                                 fallback=True).ugettext

# global variable: main window
mainWindow = None

# Helper function:
# Find a file that should have been installed in .../shared/driconf
# Prefixes of __file__ are tried. And the current directory as a fallback.
def findInShared (name):
    # try all <prefix>/share/driconf/name for all prefixes of __file__
    head,tail = os.path.split (__file__)
    while head and tail:
        f = os.path.join (head, "share/driconf", name)
        if os.path.isfile (f):
            return f
        head,tail = os.path.split (head)
    # try name in the current directory
    if os.path.isfile (name):
        return name
    print "Warning: could not find %s." % name
    # nothing found
    return None

# Helper function:
# escape text that is going to be passed as markup to pango
def escapeMarkup (text):
    return text.replace ("<", "&lt;").replace (">", "&gt;")

class StockImage (gtk.Image):
    """ A stock image. """
    def __init__ (self, stock, size):
        """ Constructor. """
        gtk.Image.__init__ (self)
        self.set_from_stock (stock, size)

class WrappingCheckButton (gtk.CheckButton):
    """ Check button with a line wrapping label. """
    def __init__ (self, label, justify=gtk.JUSTIFY_LEFT, wrap=True,
                  width=-1, height=-1):
        """ Constructor. """
        gtk.CheckButton.__init__ (self)
        checkHBox = gtk.HBox()
        self.text = escapeMarkup (label)
        self.label = gtk.Label(label)
        self.label.set_justify (justify)
        self.label.set_line_wrap (wrap)
        self.label.set_size_request (width, height)
        self.label.show()
        checkHBox.pack_start (self.label, False, False, 0)
        checkHBox.show()
        self.add (checkHBox)

    def highlight (self, flag):
        """ Highlight the label. """
        if flag:
            self.label.set_markup ('<span foreground="red">' +  self.text + \
                                   '</span>')
        else:
            self.label.set_markup (self.text)

class WrappingOptionMenu (gtk.Button):
    """ Something that looks similar to a gtk.OptionMenu ...

    but can wrap the text and has a simpler interface. It acts as a
    bidirectional map from option descriptions (opt) to values (val)
    at the same time. """
    def __init__ (self, optValList, callback, justify=gtk.JUSTIFY_LEFT,
                  wrap=True, width=-1, height=-1):
        """ Constructor. """
        gtk.Button.__init__ (self)
        self.callback = callback
        self.optDict = {}
        self.valDict = {}
        for opt,val in optValList:
            self.optDict[opt] = val
            self.valDict[val] = opt
        firstOpt,firstVal = optValList[len(optValList)-1]
        self.value = firstVal
        hbox = gtk.HBox()
        arrow = gtk.Arrow (gtk.ARROW_DOWN, gtk.SHADOW_OUT)
        arrow.show()
        self.label = gtk.Label(firstOpt)
        self.label.set_justify (justify)
        self.label.set_line_wrap (wrap)
        self.label.set_size_request (width, height)
        self.label.show()
        hbox.pack_start (self.label, True, False, 5)
        hbox.pack_start (arrow, False, False, 0)
        hbox.show()
        self.add (hbox)
        self.menu = gtk.Menu()
        for opt,val in optValList:
            item = gtk.MenuItem (opt)
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
        if event.type == gtk.gdk.BUTTON_PRESS:
            self.menu.popup(None, None, None, event.button, event.time)
            return True
        else:
            return False

    def menuSelect (self, widget, opt):
        """ React to selection of a menu item by the user. """
        self.setOpt (opt)
        self.callback (self)

class SlideSpinner (gtk.VBox):
    """ A spin button with a slider below.

    This is used for representing int and float options with a single
    range. The slider is only displayed on float options or on integer
    options with a large range (>= 20, arbitrary threshold). """
    def __init__ (self, callback, lower, upper, integer):
        gtk.VBox.__init__ (self)
        diff = upper - lower
        self.isInteger = integer
        if integer:
            step = 1
            page = (diff+4) / 5
            self.digits = 0
        else:
            self.digits = -int(math.floor(math.log10(diff) + 0.5)) + 3
            step = math.pow(10, -self.digits + 1)
            page = step * 10
            if self.digits < 0:
                self.digits = 0
        self.callback = callback
        self.adjustment = gtk.Adjustment (lower, lower, upper, step, page)
        self.spinner = gtk.SpinButton (self.adjustment, step, self.digits)
        self.spinner.set_numeric (True)
        self.spinner.show()
        self.pack_start (self.spinner, False, False, 0)
        if not integer or diff >= 20:
            self.slider = gtk.HScale (self.adjustment)
            self.slider.set_size_request (200, -1)
            self.slider.set_draw_value (False)
            self.slider.show()
            self.pack_start (self.slider, False, False, 0)
        self.adjConn = self.adjustment.connect ("value-changed", callback)

    def getValue (self):
        self.spinner.update()
        if self.isInteger:
            return int(self.adjustment.get_value())
        else:
            return self.adjustment.get_value()

    def setValue (self, value):
        self.adjustment.disconnect (self.adjConn)
        self.adjustment.set_value (value)
        self.adjConn = self.adjustment.connect ("value-changed", self.callback)

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
        self.check = WrappingCheckButton (desc, width=200)
        self.check.set_active (page.app.options.has_key (opt.name))
        self.check.set_sensitive (page.app.device.config.writable)
        self.check.connect ("clicked", self.checkOpt)
        tooltipString = str(opt)
        page.tooltips.set_tip (self.check, tooltipString)
        self.check.show()
        page.table.attach (self.check, 0, 1, i, i+1,
                           gtk.EXPAND|gtk.FILL, 0, 5, 5)
        # a button to reset the option to its default value
        sensitive = self.check.get_active() and page.app.device.config.writable
        self.resetButton = gtk.Button ()
        pixmap = StockImage ("gtk-undo", gtk.ICON_SIZE_SMALL_TOOLBAR)
        pixmap.show()
        self.resetButton.add (pixmap)
        self.resetButton.set_relief (gtk.RELIEF_NONE)
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
                self.isValid = False
            if not self.isValid:
                value = page.app.options[opt.name]
        else:
            value = opt.default
            self.isValid = True
        # the widget for editing the option value
        self.initWidget (opt, value)
        self.widget.set_sensitive (sensitive)
        page.table.attach (self.widget, 1, 2, i, i+1, gtk.FILL, 0, 5, 5)

    def initWidget (self, opt, value):
        """ Initialize the option widget.

        The widget type is selected automatically based in the option type
        and the set/range of valid values. """
        type = opt.type
        if not self.isValid:
            type = "invalid"
        if type == "bool":
            self.widget = gtk.ToggleButton ()
            self.widget.set_use_stock (True)
            if value:
                self.widget.set_label ("gtk-yes")
            else:
                self.widget.set_label ("gtk-no")
            self.widget.set_active (value)
            self.widget.connect ("toggled", self.activateSignal)
        elif type == "int" and opt.valid and len(opt.valid) == 1:
            self.widget = SlideSpinner (self.activateSignal, opt.valid[0].start,
                                        opt.valid[0].end, True)
            self.widget.setValue (value)
        elif type == "float" and opt.valid and len(opt.valid) == 1:
            self.widget = SlideSpinner (self.activateSignal, opt.valid[0].start,
                                        opt.valid[0].end, False)
            self.widget.setValue (value)
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
                            string = desc.enums[v]
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
            self.widget = gtk.Entry ()
            if type == "invalid":
                self.widget.set_text (value)
            else:
                self.widget.set_text (dri.ValueToStr(value, type))
            self.widget.connect ("changed", self.activateSignal)
        self.highlightInvalid()
        self.widget.show()

    def updateWidget (self, value, valid):
        """ Update the option widget to a new value. """
        if self.widget.__class__ == gtk.ToggleButton:
            self.widget.set_active (value)
        elif self.widget.__class__ == SlideSpinner:
            self.widget.setValue (value)
        elif self.widget.__class__ == WrappingOptionMenu:
            self.widget.setValue(str(value))
        elif self.widget.__class__ == gtk.Entry:
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
        elif self.widget.__class__ == gtk.ToggleButton:
            if self.widget.get_active():
                return "true"
            else:
                return "false"
        elif self.widget.__class__ == SlideSpinner:
            return str(self.widget.getValue())
        elif self.widget.__class__ == WrappingOptionMenu:
            return self.widget.getValue()
        elif self.widget.__class__ == gtk.Entry:
            return self.widget.get_text()
        else:
            return None

    def checkOpt (self, widget):
        """ Handler for 'check button (maybe) toggled'. """
        if self.check.get_active():
            self.widget.set_sensitive (True)
            self.resetButton.set_sensitive (True)
        else:
            self.widget.set_sensitive (False)
            self.resetButton.set_sensitive (False)
        if not self.isValid:
            self.highlightInvalid()
            self.page.doValidate()
        self.page.optionModified (self)

    def activateSignal (self, widget, dummy=None):
        """ Handler for 'widget was activated by the user'. """
        if self.widget.__class__ == gtk.ToggleButton:
            value = self.widget.get_active()
            if value:
                self.widget.set_label ("gtk-yes")
            else:
                self.widget.set_label ("gtk-no")
        self.doValidate()
        self.page.optionModified (self)

    def resetOpt (self, widget):
        """ Reset to default value. """
        self.updateWidget (self.opt.default, True)
        self.page.optionModified (self)

    def doValidate (self):
        """ Validate the current value from the option widget.

        This is only interesting if the check button is active. Only
        gtk.Entry widgets should ever give invalid values in practice.
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
        self.check.highlight (not self.isValid and self.check.get_active())

    def validate (self):
        return self.isValid or not self.check.get_active()

class SectionPage (gtk.ScrolledWindow):
    """ One page in the DriverPanel with one OptionLine per option. """
    def __init__ (self, optSection, app):
        """ Constructor. """
        gtk.ScrolledWindow.__init__ (self)
        self.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.optSection = optSection
        self.app = app
        self.tooltips = gtk.Tooltips()
        self.table = gtk.Table (len(optSection.optList), 3)
        self.optLines = []
        for i in range (len(optSection.optList)):
            self.optLines.append (OptionLine (self, i, optSection.optList[i]))
        self.table.show()
        self.add_with_viewport (self.table)
        self.doValidate (init=True)

    def optionModified (self, optLine):
        """ Callback that is invoked by changed option lines. """
        self.app.modified(self.app)

    def doValidate (self, init=False):
        """ Validate the widget settings.

        The return value indicates if there are invalid option values. """
        valid = True
        for optLine in self.optLines:
            if not optLine.validate():
                valid = False
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
                self.app.modified(self.app)
            elif value != None:
                if not self.app.options.has_key(name) or \
                   (self.app.options.has_key(name) and \
                    value != self.app.options[name]):
                    self.app.modified(self.app)
                self.app.options[name] = value

class UnknownSectionPage(gtk.VBox):
    """ Special section page for options unknown to the driver. """
    def __init__ (self, driver, app):
        """ Constructor. """
        gtk.VBox.__init__ (self)
        scrolledWindow = gtk.ScrolledWindow ()
        scrolledWindow.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.app = app
        self.driver = driver
        # copy options (dict function does not exist in Python 2.1 :( )
        opts = {}
        for name,val in app.options.items():
            opts[name] = val
        # remove all options known to the driver
        self.driverOpts = {}
        if driver:
            for sect in driver.optSections:
                for opt in sect.optList:
                    self.driverOpts[opt.name] = opt
                    if opts.has_key (opt.name):
                        del opts[opt.name]
        # short cut
        self.opts = []
        if driver and len(opts) == 0:
            return
        # list all remaining options here
        self.store = gtk.ListStore (gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)
        self.view = gtk.TreeView (self.store)
        self.view.set_rules_hint (True)
        optionRenderer = gtk.CellRendererText()
        optionRenderer.connect ("edited", self.editedSignal, 0)
        column = gtk.TreeViewColumn (_("Option"), optionRenderer,
                                     text=0, editable=2)
        self.view.append_column (column)
        valueRenderer = gtk.CellRendererText()
        valueRenderer.connect ("edited", self.editedSignal, 1)
        column = gtk.TreeViewColumn (_("Value"), valueRenderer,
                                     text=1, editable=2)
        self.view.append_column (column)
        self.view.get_selection().set_mode (gtk.SELECTION_MULTIPLE)
        for name,val in opts.items():
            self.store.set (self.store.append(),
                            0, str(name), 1, str(val), 2, True)
            self.opts.append (name)
        self.view.show()
        scrolledWindow.add (self.view)
        scrolledWindow.show()
        self.pack_start (scrolledWindow, True, True, 0)
        buttonBox = gtk.HButtonBox()
        buttonBox.set_layout (gtk.BUTTONBOX_END)
        newButton = gtk.Button (stock="gtk-new")
        newButton.connect ("clicked", self.newSetting)
        newButton.show()
        buttonBox.add (newButton)
        deleteButton = gtk.Button (stock="gtk-delete")
        deleteButton.connect ("clicked", self.deleteSelection)
        deleteButton.show()
        buttonBox.add (deleteButton)
        helpButton = gtk.Button (stock="gtk-help")
        helpButton.connect ("clicked", self.help)
        helpButton.show()
        buttonBox.add (helpButton)
        buttonBox.set_child_secondary (helpButton, True)
        buttonBox.show()
        self.pack_start (buttonBox, False, False, 0)

    def validate (self):
        """ These options can't be validated. """
        return True

    def commit (self):
        """ These options are never changed. """
        pass

    def deleteSelection (self, widget):
        """ Delete the selected items from the list and app config. """
        # Damn it! gtk.TreeSelection.get_selected_rows doesn't exist.
        # So we iterate over the whole list store and delete all selected
        # items.
        cur = self.store.get_iter_first()
        i = 0
        while cur:
            next = self.store.iter_next (cur)
            if self.view.get_selection().iter_is_selected (cur):
                name = self.store.get_value (cur, 0)
                del self.app.options[name]
                del self.opts[i]
                self.store.remove (cur)
                self.app.modified(self.app)
            else:
                i = i + 1
            cur = next

    def newSetting (self, widget):
        """ Create a new setting. Choose a unique option name, that is
        unknown to the driver. """
        name = "option"
        val = ""
        i = 0
        while self.app.options.has_key(name) or \
                  self.driverOpts.has_key(name):
            i = i + 1
            name = "option%d" % i
        self.app.options[name] = val
        self.opts.append (name)
        self.store.set (self.store.append(), 0, str(name), 1, str(val), 2, True)
        self.app.modified(self.app)

    def help (self, widget):
        if self.driver:
            msg = _("Some settings in this application configuration are "
                    "unknown to the driver. Maybe the driver version changed "
                    "and does not support these options any more. It is "
                    "probably safe to delete these settings.")
        else:
            msg = _("The driver for this device could not be determined or "
                    "does not support configuration. You can still change "
                    "the settings but it cannot be verified whether they are "
                    "supported and valid.")
        dialog = gtk.MessageDialog (
            mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, msg)
        dialog.connect ("response", lambda d,r: d.destroy())
        dialog.show()

    def editedSignal (self, widget, row, newVal, value):
        row = int(row)
        name = self.opts[row]
        cursor = self.store.get_iter_first()
        for i in range(row): cursor = self.store.iter_next (cursor)
        if value:
            if self.app.options[name] == newVal:
                return
            self.app.options[name] = newVal
            self.store.set (cursor, 0, str(name), 1, str(newVal), 2, True)
        else:
            if name == newVal or self.app.options.has_key(newVal) or \
                   self.driverOpts.has_key(newVal):
                return
            val = self.app.options.pop(name)
            name = newVal
            self.opts[row] = name
            self.app.options[name] = val
            self.store.set (cursor, 0, str(name), 1, str(val), 2, True)
        self.app.modified(self.app)

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
                sectPage = SectionPage (sect, app)
                sectPage.show()
                desc = sect.getDesc([lang])
                if desc:
                    if len(desc) > 30:
                        # Truncate long section descriptions and add a
                        # tooltip with the full description.
                        # Eek: need an event box since tooltips don't work
                        # on labels.
                        try:
                            space = desc[20:].index(' ') + 20
                            if space < 30:
                                shortDesc = desc[:space]
                            else:
                                shortDesc = desc[:30]
                        except ValueError:
                            shortDesc = desc[:30]
                        labelWidget = gtk.EventBox()
                        tooltips.set_tip (labelWidget, desc)
                        sectLabel = gtk.Label (shortDesc + " ...")
                        sectLabel.show()
                        labelWidget.add (sectLabel)
                    else:
                        sectLabel = gtk.Label (desc)
                        labelWidget = sectLabel
                else:
                    sectLabel = gtk.Label (_("(no description)"))
                    labelWidget = sectLabel
                labelWidget.show()
                notebook.append_page (sectPage, labelWidget)
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
        gtk.Dialog.__init__ (self, title, mainWindow,
                             gtk.DIALOG_DESTROY_WITH_PARENT|gtk.DIALOG_MODAL,
                             (gtk.STOCK_OK, gtk.RESPONSE_OK,
                              gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.callback = callback
        self.data = data
        self.connect ("response", self.responseSignal)
        table = gtk.Table(2, 2)
        commentLabel = gtk.Label (_(
            "Enter the name of the application below. This serves just a "
            "descriptivion for you. Don't forget to set the executable "
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
        gtk.Dialog.__init__ (self, title, mainWindow,
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
            [""]+map(str,range(len(dpy.screens))))
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
            screen = dpy.getScreen(screenNum)
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
            curNode = mainWindow.configTree.getSelection (allowNone=True)
            if not curNode:
                mainWindow.deactivateButtons()
            elif curNode.__class__ == dri.DRIConfig:
                mainWindow.activateConfigButtons(curNode)
            elif curNode.__class__ == dri.DeviceConfig:
                mainWindow.activateDeviceButtons(curNode)
            elif curNode.__class__ == dri.AppConfig:
                mainWindow.activateAppButtons(curNode)

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
            driver = app.device.getDriver(dpy)
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
                driver = app.device.getDriver (dpy)
            except dri.XMLError, problem:
                driver = None
                dialog = gtk.MessageDialog (
                    mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                    _("Parsing the driver's configuration information: %s") %
                    problem)
                dialog.connect ("response", lambda d,r: d.destroy())
                dialog.show()
        else:
            driver = None
            app = None
        mainWindow.commitDriverPanel()
        mainWindow.switchDriverPanel (driver, app)
        if not node:
            mainWindow.deactivateButtons()
        elif node.__class__ == dri.DRIConfig:
            mainWindow.activateConfigButtons(node)
        elif node.__class__ == dri.DeviceConfig:
            mainWindow.activateDeviceButtons(node)
        elif node.__class__ == dri.AppConfig:
            mainWindow.activateAppButtons(node)

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
                mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                _("Really delete application \"%s\"?") % node.name)
        elif node.__class__ == dri.DeviceConfig:
            parent = node.config
            dialog = gtk.MessageDialog (
                mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
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
            mainWindow.removeApp (node)
        elif node.__class__ == dri.DeviceConfig:
            for app in node.apps:
                mainWindow.removeApp (app)
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
                driver = device.getDriver (dpy)
            except dri.XMLError:
                driver = None
            if driver == None:
                continue
            for app in device.apps:
                valid = valid and driver.validate (app.options)
        if not valid:
            dialog = gtk.MessageDialog (
                mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
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
                mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                _("Can't open \"%s\" for writing.") % config.fileName)
            dialog.run()
            dialog.destroy()
            return
        mainWindow.commitDriverPanel()
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
            mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
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
                mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
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
                mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
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
        newConfig.writable = fileIsWritable (config.fileName)
        # find the position of config
        configList = self.getConfigList()
        index = configList.index (config)
        if index == len(configList)-1:
            sibling = None
        else:
            sibling = configList[index+1]
        if node.__class__ == dri.AppConfig:
            mainWindow.removeApp (node)
        elif node.__class__ == dri.DeviceConfig:
            for app in node.apps:
                mainWindow.removeApp (app)
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
        mainWindow.renameApp (app)
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
        writable = app.device.config.writable
        modified = app.device.config.isModified
        self.saveButton      .set_sensitive (writable and modified)
        self.reloadButton    .set_sensitive (True)
        self.newButton       .set_sensitive (writable)
        self.removeButton    .set_sensitive (writable)
        self.upButton        .set_sensitive (writable)
        self.downButton      .set_sensitive (writable)
        self.propertiesButton.set_sensitive (writable)

    def aboutHandler (self, widget):
        version = "0.2.6"
        translators = _("translator-credits")
        if translators == "translator-credits":
            translators = None
        if gtk.__dict__.has_key("AboutDialog"):
            dialog = gtk.AboutDialog()
            dialog.set_name("DRIconf")
            dialog.set_version(version)
            dialog.set_copyright(u"Copyright \u00a9 2003-2005  "
                                 u"Felix K\u00fchling")
            dialog.set_comments(_("A configuration GUI for DRI drivers"))
            dialog.set_website(u"http://dri.freedesktop.org/wiki/DriConf")
            if translators:
                dialog.set_translator_credits(translators)
            else:
                dialog.set_translator_credits("hi")
            logoPath = findInShared("drilogo.jpg")
            if logoPath:
                logo = gtk.gdk.pixbuf_new_from_file (logoPath)
                dialog.set_logo(logo)
        else:
            text = u"DRIconf %s\n" \
                   u"%s\n" \
                   u"Copyright \u00a9 2003-2005  Felix K\u00fchling\n" \
                   u"\n" \
                   u"http://dri.freedesktop.org/wiki/DriConf" \
                   % (version,  _("A configuration GUI for DRI drivers"))
            if translators:
                text = text + (u"\n\n%s: %s" % (_("Translated by"),
                                              _("translator-credits")))
            dialog = gtk.MessageDialog (
                mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT|gtk.DIALOG_MODAL,
                gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, text)
            dialog.set_title(_("About DRIconf"))
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
                mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT|gtk.DIALOG_MODAL,
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
        dialog = gtk.MessageDialog (None, 0, gtk.MESSAGE_ERROR,
                                    gtk.BUTTONS_OK, str(problem))
        dialog.run()
        dialog.destroy()
        return
    except dri.XMLError, problem:
        dialog = gtk.MessageDialog (
            None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
            _("There are errors in a driver's configuration information:\n"
              "%s\n"
              "This should not happen. It probably means that you have to "
              "update DRIconf.") % str(problem))
        dialog.run()
        dialog.destroy()
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
                config.writable = fileIsWritable (fileName)
            cfile.close()
        if config:
            configList.append (config)

    # open the main window
    # initSelection must be called before and after mainWindow.show().
    # Before makes sure that the initial window size is correct.
    # After is needed since the selection seems to get lost in
    # mainWindow.show().
    global mainWindow
    mainWindow = MainWindow(configList)
    mainWindow.set_default_size (750, 375)
    mainWindow.initSelection()
    mainWindow.show ()
    mainWindow.initSelection()

    if len(newFiles) == 1:
        dialog = gtk.MessageDialog (
            mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
            _("Created a new DRI configuration file \"%s\" for you.")
            % newFiles[0])
        dialog.run()
        dialog.destroy()
    elif len(newFiles) > 1:
        dialog = gtk.MessageDialog (
            mainWindow, gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
            _("Created new DRI configuration files %s for you.") %
            reduce(lambda a, b: str(a) + ", " + str(b),
                   map (lambda a: "\"%s\"" % str(a), newFiles)))
        dialog.run()
        dialog.destroy()

    # run
    gtk.main()
