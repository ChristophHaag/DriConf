# DRI configuration GUI: common UI components and helpers, global vars

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
import locale
import gettext
import math
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

# global variable: lang
locale.setlocale(locale.LC_ALL, '')
lang,encoding = locale.getlocale(locale.LC_MESSAGES)
if lang:
    underscore = lang.find ('_')
    if underscore != -1:
        lang = lang[0:underscore]
else:
    lang = "en"
# encoding is only a dummy. Pango uses UTF-8 everywhere. :)
del encoding

# global variable: version
version = "0.9.0"

# global variable: dpy
dpy = None

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

def fileIsWritable(filename):
    """ Find out if a file is writable.

    Returns True for existing writable files, False otherwise. """
    try:
        fd = os.open (filename, os.O_WRONLY)
    except OSError:
        return False
    if fd == -1:
        return False
    else:
        os.close (fd)
        return True

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

class WrappingLabel (gtk.Label):
    """ Line wrapping label with a highlight method """
    def __init__ (self, label, justify=gtk.JUSTIFY_LEFT, wrap=True,
                  width=-1, height=-1):
        self.text = escapeMarkup (label)
        gtk.Label.__init__ (self, label)
        self.set_justify (justify)
        self.set_line_wrap (wrap)
        self.set_size_request (width, height)

    def highlight (self, flag):
        """ Highlight the label. """
        if flag:
            self.set_markup ('<span foreground="red">' +  self.text + \
                             '</span>')
        else:
            self.set_markup (self.text)

class WrappingDummyCheckButton (gtk.HBox):
    """ Dummy Check button with a line wrapping label. """
    def __init__ (self, label, justify=gtk.JUSTIFY_LEFT, wrap=True,
                  width=-1, height=-1):
        """ Constructor. """
        gtk.HBox.__init__ (self)
        self.text = escapeMarkup (label)
        self.label = WrappingLabel (label, justify, wrap, width, height)
        self.label.show()
        self.pack_start (self.label, False, False, 0)

    def highlight (self, flag):
        """ Highlight the label. """
        self.label.highlight (flag)

    def get_active (self):
        """ Hack: make it behave like a check button ...

        ... to some extent such that OptionLine does not need to
        distinguish between simple and complex mode. """
        return True

class WrappingCheckButton (gtk.CheckButton):
    """ Check button with a line wrapping label. """
    def __init__ (self, label, justify=gtk.JUSTIFY_LEFT, wrap=True,
                  width=-1, height=-1):
        """ Constructor. """
        gtk.CheckButton.__init__ (self)
        checkHBox = gtk.HBox()
        self.text = escapeMarkup (label)
        self.label = WrappingLabel (label, justify, wrap, width, height)
        self.label.show()
        checkHBox.pack_start (self.label, False, False, 0)
        checkHBox.show()
        self.add (checkHBox)

    def highlight (self, flag):
        """ Highlight the label. """
        self.label.highlight (flag)

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
    def __init__ (self, page, i, opt, simple, removable = False):
        """ Constructor. """
        self.page = page
        self.opt = opt
        self.index = i
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
        if simple:
            self.label = WrappingDummyCheckButton (desc, width=200)
        else:
            self.label = WrappingCheckButton (desc, width=200)
            self.label.set_active (page.app.options.has_key (opt.name))
            self.label.set_sensitive (page.app.device.config.writable)
            self.label.connect ("clicked", self.checkOpt)
        tooltipString = str(opt)
        page.tooltips.set_tip (self.label, tooltipString)
        self.label.show()
        page.table.attach (self.label, 0, 1, i, i+1,
                           gtk.EXPAND|gtk.FILL, 0, 5, 5)
        # a button to reset the option to its default value
        sensitive = self.label.get_active() and page.app.device.config.writable
        self.resetButton = gtk.Button ()
        if removable:
            pixmap = StockImage ("gtk-remove", gtk.ICON_SIZE_SMALL_TOOLBAR)
        else:
            pixmap = StockImage ("gtk-undo", gtk.ICON_SIZE_SMALL_TOOLBAR)
        pixmap.show()
        self.resetButton.add (pixmap)
        self.resetButton.set_relief (gtk.RELIEF_NONE)
        self.resetButton.set_sensitive (sensitive)
        if removable:
            page.tooltips.set_tip(self.resetButton, _("Remove"))
            self.resetButton.connect ("clicked", self.removeOpt)
        else:
            page.tooltips.set_tip(self.resetButton, _("Reset to default value"))
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
        if not self.label.get_active():
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
        if self.label.get_active():
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

    def removeOpt (self, widget):
        """ Reset to default value. """
        self.page.removeOption (self, self.opt)

    def doValidate (self):
        """ Validate the current value from the option widget.

        This is only interesting if the check button is active. Only
        gtk.Entry widgets should ever give invalid values in practice.
        Invalid option widgets are highlighted. If the validity
        changed, reinitialize the widget and have the page check if
        its validity was changed, too. """
        value = self.getValue()
        if value == None:
            return
        valid = self.opt.validate (value)
        if (valid and not self.isValid) or (not valid and self.isValid):
            self.isValid = valid
            self.highlightInvalid()
            # Re-init the widget.
            i = self.index
            self.page.table.remove(self.widget)
            self.widget.destroy()
            self.initWidget(self.opt, dri.StrToValue(value, self.opt.type))
            self.widget.show()
            self.page.table.attach (self.widget, 1, 2, i, i+1, gtk.FILL, 0, 5, 5)
            # Update parent page.
            self.page.doValidate()

    def highlightInvalid (self):
        self.label.highlight (not self.isValid and self.label.get_active())

    def validate (self):
        return self.isValid or not self.label.get_active()

class SectionPage (gtk.ScrolledWindow):
    """ One page in the DriverPanel with one OptionLine per option. """
    def __init__ (self, optSection, app, simple):
        """ Constructor. """
        gtk.ScrolledWindow.__init__ (self)
        self.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.optSection = optSection
        self.app = app
        self.simple = simple
        self.tooltips = gtk.Tooltips()
        self.table = gtk.Table (len(optSection.optList), 3)
        self.optLines = []
        for i in range (len(optSection.optList)):
            self.optLines.append (OptionLine (self, i, optSection.optList[i], simple))
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
            elif value != None:
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
                            0, str(name), 1, str(val),
                            2, app.device.config.writable)
            self.opts.append (name)
        self.view.show()
        scrolledWindow.add (self.view)
        scrolledWindow.show()
        self.pack_start (scrolledWindow, True, True, 0)
        buttonBox = gtk.HButtonBox()
        buttonBox.set_layout (gtk.BUTTONBOX_END)
        if not self.driver:
            newButton = gtk.Button (stock="gtk-add")
            newButton.connect ("clicked", self.newSetting)
            newButton.set_sensitive(app.device.config.writable)
            newButton.show()
            buttonBox.add (newButton)
        deleteButton = gtk.Button (stock="gtk-remove")
        deleteButton.connect ("clicked", self.deleteSelection)
        deleteButton.set_sensitive(app.device.config.writable)
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

if gtk.__dict__.has_key("AboutDialog"):
    # About Dialog was added in gtk 2.6.
    class AboutDialog (gtk.AboutDialog):
        def __init__ (self):
            gtk.AboutDialog.__init__(self)
            translators = _("translator-credits")
            if translators == "translator-credits":
                translators = None
            self.set_name("DRIconf")
            self.set_version(version)
            self.set_copyright(u"Copyright \u00a9 2003-2005  "
                               u"Felix K\u00fchling")
            self.set_comments(_("A configuration applet for DRI drivers"))
            self.set_website(u"http://dri.freedesktop.org/wiki/DriConf")
            if translators:
                self.set_translator_credits(translators)
            logoPath = findInShared("drilogo.jpg")
            if logoPath:
                logo = gtk.gdk.pixbuf_new_from_file (logoPath)
                self.set_logo(logo)
else:
    class AboutDialog (gtk.MessageDialog):
        def __init__ (self):
            translators = _("translator-credits")
            if translators == "translator-credits":
                translators = None
            text = u"DRIconf %s\n" \
                   u"%s\n" \
                   u"Copyright \u00a9 2003-2005  Felix K\u00fchling\n" \
                   u"\n" \
                   u"http://dri.freedesktop.org/wiki/DriConf" \
                   % (version,  _("A configuration applet for DRI drivers"))
            if translators:
                text = text + (u"\n\n%s: %s" % (_("Translated by"),
                                              _("translator-credits")))
            gtk.MessageDialog.__init__(
                self, mainWindow,
                gtk.DIALOG_DESTROY_WITH_PARENT|gtk.DIALOG_MODAL,
                gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, text)
            self.set_title(_("About DRIconf"))
