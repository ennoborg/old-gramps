# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
# Copyright (C) 2010       Jakim Friant
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id$

"""Tools/Database Processing/Merge Place Data"""

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
import re
from gen.ggettext import gettext as _
from gen.ggettext import ngettext

#-------------------------------------------------------------------------
#
# gnome/gtk
#
#-------------------------------------------------------------------------
import gtk
import gobject

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
from gen.db import DbTxn
import ManagedWindow
import GrampsDisplay

from gui.plug import tool
from QuestionDialog import OkDialog
from gui.utils import ProgressMeter
from glade import Glade

from Errors import MergeError
from Merge import MergePlaceQuery

COLS = [ 
    (_('Place title'), 1), 
    (_('City'), 2), 
    (_('State'), 3), 
    (_('ZIP/Postal Code'), 4), 
    (_('Country'), 5)
    ]

#-------------------------------------------------------------------------
#
# MergePlaces
#
#-------------------------------------------------------------------------
class MergePlaces(tool.BatchTool, ManagedWindow.ManagedWindow):
    """
    Extracts city, state, and zip code information from an place description
    if the title is empty and the description falls into the category of:

       New York, NY 10000

    Sorry for those not in the US or Canada. I doubt this will work for any
    other locales.
    Works for Sweden if the decriptions is like
        Stockholm (A)
    where the letter A is the abbreviation letter for laen.
    Works for France if the description is like
        Paris, IDF 75000, FRA
    or  Paris, ILE DE FRANCE 75000, FRA
    """

    def __init__(self, dbstate, uistate, options_class, name, callback=None):
        self.label = _('Merge Place data')
        self.dbstate = dbstate
        
        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self.__class__)
        self.set_window(gtk.Window(), gtk.Label(), '')

        tool.BatchTool.__init__(self, dbstate, uistate, options_class, name)

        if not self.fail:
            uistate.set_busy_cursor(True)
            self.run(dbstate.db)
            uistate.set_busy_cursor(False)

    def run(self, db):
        """
        Performs the actual extraction of information
        """

        self.progress = ProgressMeter(_('Checking Place Titles'), '')
        self.progress.set_pass(_('Looking for place fields'), 
                               self.db.get_number_of_places())

        self.name_list = []

        db.disable_signals()
        num_merges = 0
        for place in db.iter_places():
            descr = place.get_title()
            loc = place.get_main_location()
            self.progress.step()

            if loc.get_street() == loc.get_city() == \
               loc.get_state() == loc.get_postal_code() == "":

                for match_place in db.iter_places():
                    match_descr = match_place.get_title()
                    match_loc = match_place.get_main_location()

                    if descr == match_descr and place.get_handle() != match_place.get_handle() \
                      and match_loc.get_street() == match_loc.get_city() == \
                          match_loc.get_state() == match_loc.get_postal_code() == "":

                        print descr
                        query = MergePlaceQuery(
                                self.dbstate, place, match_place)
                        query.execute()
                        num_merges += 1

        db.enable_signals()
        db.request_rebuild()
        self.progress.close()
        OkDialog(
            _("Number of merges done"),
            ngettext("%(num)d places merged",
            "%(num)d places merged", num_merges) % {'num': num_merges})
        self.close()

    def display(self):

        self.top = Glade("changenames.glade")
        window = self.top.toplevel
        self.top.connect_signals({
            "destroy_passed_object" : self.close, 
            "on_ok_clicked" : self.on_ok_clicked, 
            "on_help_clicked" : self.on_help_clicked, 
            "on_delete_event"   : self.close,
            })
        
        self.list = self.top.get_object("list")
        self.set_window(window, self.top.get_object('title'), self.label)
        lbl = self.top.get_object('info')
        lbl.set_line_wrap(True)
        lbl.set_text(
            _('Below is a list of Places with the possible data that can '
              'be extracted from the place title. Select the places you '
              'wish Gramps to convert.'))

        self.model = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, 
                                   gobject.TYPE_STRING, gobject.TYPE_STRING, 
                                   gobject.TYPE_STRING, gobject.TYPE_STRING, 
                                   gobject.TYPE_STRING)

        r = gtk.CellRendererToggle()
        r.connect('toggled', self.toggled)
        c = gtk.TreeViewColumn(_('Select'), r, active=0)
        self.list.append_column(c)

        for (title, col) in COLS:
            render = gtk.CellRendererText()
            if col > 1:
                render.set_property('editable', True)
                render.connect('edited', self.__change_name, col)
            
            self.list.append_column(
                gtk.TreeViewColumn(title, render, text=col))
        self.list.set_model(self.model)

        self.iter_list = []
        self.progress.set_pass(_('Building display'), len(self.name_list))
        for (id, data) in self.name_list:

            place = self.db.get_place_from_handle(id)
            descr = place.get_title()

            handle = self.model.append()
            self.model.set_value(handle, 0, False)
            self.model.set_value(handle, 1, descr)
            if data[0]:
                self.model.set_value(handle, 2, data[0])
            if data[1]:
                self.model.set_value(handle, 3, data[1])
            if data[2]:
                self.model.set_value(handle, 4, data[2])
            if data[3]:
                self.model.set_value(handle, 5, data[3])
            self.model.set_value(handle, 6, id)
            self.iter_list.append(handle)
            self.progress.step()
        self.progress.close()
            
        self.show()

    def __change_name(self, text, path, new_text, col):
        self.model[path][col] = new_text
        return

    def toggled(self, cell, path_string):
        path = tuple(map(int, path_string.split(':')))
        row = self.model[path]
        row[0] = not row[0]

    def build_menu_names(self, obj):
        return (self.label, None)

    def on_help_clicked(self, obj):
        """Display the relevant portion of GRAMPS manual"""
        GrampsDisplay.help()

    def on_ok_clicked(self, obj):
        with DbTxn(_("Merge Place data"), self.db, batch=True) as self.trans:
            self.db.disable_signals()
            changelist = [node for node in self.iter_list
                          if self.model.get_value(node, 0)]

            for change in changelist:
                row = self.model[change]
                place = self.db.get_place_from_handle(row[6])
                (city, state, postal, country) = (row[2], row[3], row[4], row[5])

                if city:
                    place.get_main_location().set_city(city)
                if state:
                    place.get_main_location().set_state(state)
                if postal:
                    place.get_main_location().set_postal_code(postal)
                if country:
                    place.get_main_location().set_country(country)
                self.db.commit_place(place, self.trans)

        self.db.enable_signals()
        self.db.request_rebuild()
        self.close()
        
#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class MergePlacesOptions(tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """
    def __init__(self, name, person_id=None):
        tool.ToolOptions.__init__(self, name, person_id)
