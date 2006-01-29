# DRI configuration GUI: OpenGL application database

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

import types
import pygtk
pygtk.require ("2.0")
import gtk
import gobject

import driconf_commonui

from driconf_commonui import _

GamesSim = {
    "FlightGear" : "fgfs",
    "Torcs" : "torcs-bin"
}

GamesArcade = {
    "Neverball" : "neverball",
    "Neverputt" : "neverputt",
    "Chromium BSU" : "chromium",
    "BZFlag" : "bzflag",
    "TuxKart" : "tuxkart",
    "Tux Racer" : "tuxracer",
    "PlanetPenguin Racer" : "ppracer",
    "SuperTux" : "supertux"
}

GamesShooter = {
    "Quake III Demo (x86)" : "q3demo.x86"
}

GamesStrategy = {
}

GamesRPG = {
}

Games = {
    _("Arcade") : GamesArcade,
    _("Simulation") : GamesSim,
    _("Ego-Shooter") : GamesShooter,
    _("Strategy") : GamesStrategy,
    _("Role Playing and Adventure") : GamesRPG
}

ScienceEng = {
    "Celestia (KDE)" : "celestia",
    "Celestia (GNOME)" : "celestia-gnome"
}

ModelRender = {
    "Blender" : "blender"
}

Media = {
    "MPlayer" : "mplayer"
}

Benchmarks = {
    "GLX Gears is not a benchmark" : "glxgears",
    "Glean" : "glean"
}

AppDB = {
    _("Games") : Games,
    _("Science and Engineering") : ScienceEng,
    _("Modelling and Rendering") : ModelRender,
    _("Multimedia") : Media,
    _("Benchmarks") : Benchmarks
}

# Constants

# Types of application menu entries. Positive numbers are reserved for
# application indices used by the UI.
PREDEF_CATEGORY = -1
PREDEF_APP = -2
CUSTOM_APP = -3
SEPARATOR = -4

# Columns in the TreeStore (COL_TYPE == COL_INDEX is intentional, see above)
COL_NAME = 0
COL_EXEC = 1
COL_TYPE = 2
COL_INDEX = 2

def addToTreeStore (treestore, parent, dictionary):
    keys = dictionary.keys()
    keys.sort()
    for key in keys:
        value = dictionary[key]
        if type(value) is types.DictType:
            if value:
                node = treestore.append(parent, [key, "", PREDEF_CATEGORY])
                addToTreeStore(treestore, node, value)
        else:
            node = treestore.append(parent, [key, value, PREDEF_APP])

def createTreeStore ():
    treestore = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
                              gobject.TYPE_INT)
    addToTreeStore (treestore, None, AppDB)
    return treestore

def isSeparator (model, it):
    return model.get_value(it, COL_TYPE) == SEPARATOR
