#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000  Donald N. Allingham
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


#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import sys
import string
import re
import os

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
from gtk import *
from gnome.ui import *

import GTK
import gnome.config
import gnome.help
import libglade

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
from RelLib import *

import Researcher
import const
import utils
import ListColors
import intl

_ = intl.gettext

_date_format_list = [
    "Month Day, Year",
    "MON Day, Year",
    "Day MON Year",
    "MM/DD/YY",
    "MM-DD-YY",
    "DD/MM/YY",
    "DD-MM-YY"
    ]

_date_entry_list = [
    "MM/DD/YY",
    "DD/MM/YY"
    ]

_name_format_list = [
    (_("Firstname Surname"), utils.normal_name),
    (_("Surname, Firstname"), utils.phonebook_name),
    ]

#-------------------------------------------------------------------------
#
# Visible globals
#
#-------------------------------------------------------------------------

owner         = Researcher.Researcher()
autoload      = 0
usetabs       = 0
hide_altnames = 0
lastfile      = None
nameof        = utils.normal_name
display_attr  = 0
attr_name     = ""

#-------------------------------------------------------------------------
#
# Globals
#
#-------------------------------------------------------------------------
_name_format  = 0
_callback     = None
_druid        = None

#-------------------------------------------------------------------------
#
# Constants 
#
#-------------------------------------------------------------------------
ODDFGCOLOR    = "oddForeground"
ODDBGCOLOR    = "oddBackground"
EVENFGCOLOR   = "evenForeground"
EVENBGCOLOR   = "evenBackground"

#-------------------------------------------------------------------------
#
# make_path - 
#   Creates a directory if it does not already exist. Assumes that the
#   parent directory already exits
#
#-------------------------------------------------------------------------
def make_path(path):
    if not os.path.isdir(path):
        os.mkdir(path)

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def loadConfig(call):
    global autoload
    global owner
    global usetabs
    global hide_altnames
    global lastfile
    global nameof
    global display_attr
    global attr_name
    global _druid
    global _name_format
    global _callback

    _callback = call
    lastfile = gnome.config.get_string("/gramps/data/LastFile")
    usetabs = gnome.config.get_bool("/gramps/config/UseTabs")
    display_attr = gnome.config.get_bool("/gramps/config/DisplayAttr")
    attr_name = gnome.config.get_string("/gramps/config/DisplayAttrName")
    
    hide_altnames = gnome.config.get_bool("/gramps/config/DisplayAltNames")
    autoload = gnome.config.get_bool("/gramps/config/autoLoad")
    dateFormat = gnome.config.get_int("/gramps/config/dateFormat")
    dateEntry = gnome.config.get_int("/gramps/config/dateEntry")
    _name_format = gnome.config.get_int("/gramps/config/nameFormat")

    name = gnome.config.get_string("/gramps/researcher/name")
    addr = gnome.config.get_string("/gramps/researcher/addr")
    city = gnome.config.get_string("/gramps/researcher/city")
    state = gnome.config.get_string("/gramps/researcher/state")
    country = gnome.config.get_string("/gramps/researcher/country")
    postal = gnome.config.get_string("/gramps/researcher/postal")
    phone = gnome.config.get_string("/gramps/researcher/phone")
    email = gnome.config.get_string("/gramps/researcher/email")

    ListColors.enable = gnome.config.get_bool("/gramps/color/enableColors")
    if ListColors.enable == None:
        ListColors.enable = 0

    ListColors.oddfg = get_config_color(ODDFGCOLOR,(0,0,0))
    ListColors.oddbg = get_config_color(ODDBGCOLOR,(0xffff,0xffff,0xffff))
    ListColors.evenfg = get_config_color(EVENFGCOLOR,(0,0,0))
    ListColors.evenbg = get_config_color(EVENBGCOLOR,(0xffff,0xffff,0xffff))

    if display_attr == None:
        display_attr = 0

    if attr_name == None:
        attr_name = ""

    if autoload == None:
        autoload = 1
    if usetabs == None:
        usetabs = 0
    if hide_altnames == None:
        hide_altnames = 0
    if dateFormat == None:
        dateFormat = 0
    if dateEntry == None:
        dateEntry = 0

    Date.formatCode = dateFormat
    Date.entryCode = dateEntry

    if _name_format == None or _name_format == 0:
        _name_format = 0
        nameof = utils.normal_name
    else:
        nameof = utils.phonebook_name
        
    if name == None:
        _druid = libglade.GladeXML(const.configFile,"initDruid")
        _druid.signal_autoconnect({
            "destroy_passed_object" : druid_cancel_clicked,
            "on_initDruid_finish" : on_initDruid_finish
            })
    else:
        owner.set(name,addr,city,state,country,postal,phone,email)
        
    make_path(os.path.expanduser("~/.gramps"))
    make_path(os.path.expanduser("~/.gramps/filters"))
    make_path(os.path.expanduser("~/.gramps/plugins"))

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def save_last_file(file):
    gnome.config.set_string("/gramps/data/LastFile",file)
    gnome.config.sync()

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def on_initDruid_finish(obj,b):
    global owner
    
    name = _druid.get_widget("dresname").get_text()
    addr = _druid.get_widget("dresaddr").get_text()
    city = _druid.get_widget("drescity").get_text()
    state = _druid.get_widget("dresstate").get_text()
    country = _druid.get_widget("drescountry").get_text()
    postal = _druid.get_widget("drespostal").get_text()
    phone = _druid.get_widget("dresphone").get_text()
    email = _druid.get_widget("dresemail").get_text()

    owner.set(name,addr,city,state,country,postal,phone,email)
    store_researcher(owner)
    utils.destroy_passed_object(obj)

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def store_researcher(res):
    gnome.config.set_string("/gramps/researcher/name",res.name)
    gnome.config.set_string("/gramps/researcher/addr",res.addr)
    gnome.config.set_string("/gramps/researcher/city",res.city)
    gnome.config.set_string("/gramps/researcher/state",res.state)
    gnome.config.set_string("/gramps/researcher/country",res.country)
    gnome.config.set_string("/gramps/researcher/postal",res.postal)
    gnome.config.set_string("/gramps/researcher/phone",res.phone)
    gnome.config.set_string("/gramps/researcher/email",res.email)
    gnome.config.sync()
    
#-------------------------------------------------------------------------
#
# Apply values set in the property box.  For simplicity, only apply the
# values when the page is -1 (the box has been closed).
#
#-------------------------------------------------------------------------
def on_propertybox_apply(obj,page):
    global nameof
    global owner
    global usetabs
    global display_attr
    global attr_name
    global hide_altnames

    if page != -1:
        return
    
    autoload = prefsTop.get_widget("autoload").get_active()
    display_attr = prefsTop.get_widget("attr_display").get_active()
    attr_name = string.strip(prefsTop.get_widget("attr_name").get_text())
    usetabs = prefsTop.get_widget("usetabs").get_active()
    hide_altnames = prefsTop.get_widget("display_altnames").get_active()
    
    gnome.config.set_bool("/gramps/config/UseTabs",usetabs)
    gnome.config.set_bool("/gramps/config/DisplayAttr",display_attr)
    gnome.config.set_string("/gramps/config/DisplayAttrName",attr_name)
    gnome.config.set_bool("/gramps/config/autoLoad",autoload)
    gnome.config.set_bool("/gramps/config/DisplayAltNames",hide_altnames)

    # search for the active date format selection
    
    format_menu = prefsTop.get_widget("date_format").get_menu()
    active = format_menu.get_active().get_data("i")

    Date.formatCode = active
    gnome.config.set_int("/gramps/config/dateFormat",active)

    format_menu = prefsTop.get_widget("date_entry_format").get_menu()
    entry_active = format_menu.get_active().get_data("i")

    Date.entryCode = entry_active
    gnome.config.set_int("/gramps/config/dateEntry",entry_active)

    # get the name format

    format_menu = prefsTop.get_widget("name_format").get_menu()
    active_name = format_menu.get_active().get_data("i")

    name_tuple = _name_format_list[active_name]
    nameof = name_tuple[1]
    gnome.config.set_int("/gramps/config/nameFormat",active_name)

    name = prefsTop.get_widget("resname").get_text()
    addr = prefsTop.get_widget("resaddr").get_text()
    city = prefsTop.get_widget("rescity").get_text()
    state = prefsTop.get_widget("resstate").get_text()
    country = prefsTop.get_widget("rescountry").get_text()
    postal = prefsTop.get_widget("respostal").get_text()
    phone = prefsTop.get_widget("resphone").get_text()
    email = prefsTop.get_widget("resemail").get_text()

    ListColors.enable = prefsTop.get_widget("enableColors").get_active()
    gnome.config.set_bool("/gramps/color/enableColors",ListColors.enable)
    
    ListColors.oddfg = prefsTop.get_widget(ODDFGCOLOR).get_i16()
    ListColors.oddbg = prefsTop.get_widget(ODDBGCOLOR).get_i16()
    ListColors.evenfg = prefsTop.get_widget(EVENFGCOLOR).get_i16()
    ListColors.evenbg = prefsTop.get_widget(EVENBGCOLOR).get_i16()

    save_config_color(ODDFGCOLOR,ListColors.oddfg)
    save_config_color(ODDBGCOLOR,ListColors.oddbg)
    save_config_color(EVENFGCOLOR,ListColors.evenfg)
    save_config_color(EVENBGCOLOR,ListColors.evenbg)

    owner.set(name,addr,city,state,country,postal,phone,email)
    store_researcher(owner)
    
    # update the config file
    
    gnome.config.sync()
    _callback()

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def save_config_color(name,color):
    gnome.config.set_int("/gramps/color/" + name + ".r",color[0])
    gnome.config.set_int("/gramps/color/" + name + ".g",color[1])
    gnome.config.set_int("/gramps/color/" + name + ".b",color[2])

#-------------------------------------------------------------------------
#
# Called by the elements on the property box to set the changed flag,
# so that the property box knows to set the Apply button
#
#-------------------------------------------------------------------------
def on_object_toggled(obj):
    obj.changed()

#-------------------------------------------------------------------------
#
# Called by the elements on the property box to set the changed flag,
# so that the property box knows to set the Apply button
#
#-------------------------------------------------------------------------
def on_format_toggled(obj):
    obj.get_data("o").changed()

#-------------------------------------------------------------------------
#
# Called by the elements on the property box to set the changed flag,
# so that the property box knows to set the Apply button
#
#-------------------------------------------------------------------------
def on_color_toggled(obj):
    active = prefsTop.get_widget("enableColors").get_active()
    prefsTop.get_widget(ODDFGCOLOR).set_sensitive(active)
    prefsTop.get_widget(ODDBGCOLOR).set_sensitive(active)
    prefsTop.get_widget(EVENFGCOLOR).set_sensitive(active)
    prefsTop.get_widget(EVENBGCOLOR).set_sensitive(active)
    obj.changed()

#-------------------------------------------------------------------------
#
# Called by the elements on the property box to set the changed flag,
# so that the property box knows to set the Apply button
#
#-------------------------------------------------------------------------
def on_color_set(obj,r,g,b,a):
    obj.changed()

#-------------------------------------------------------------------------
#
# Create the property box, and set the elements off the current values
#
#-------------------------------------------------------------------------
def display_preferences_box():
    global prefsTop

    prefsTop = libglade.GladeXML(const.configFile,"propertybox")
    prefsTop.signal_autoconnect({
        "destroy_passed_object" : utils.destroy_passed_object,
        "on_propertybox_apply" : on_propertybox_apply,
        "on_color_toggled" : on_color_toggled,
        "on_color_set" : on_color_set,
        "on_object_toggled" : on_object_toggled
        })

    pbox = prefsTop.get_widget("propertybox")
    auto = prefsTop.get_widget("autoload")
    tabs = prefsTop.get_widget("usetabs")
    display_attr_obj = prefsTop.get_widget("attr_display")
    display_altnames = prefsTop.get_widget("display_altnames")
    auto.set_active(autoload)
    tabs.set_active(usetabs)

    display_attr_obj.set_active(display_attr)
    prefsTop.get_widget("attr_name").set_text(attr_name)
        
    display_altnames.set_active(hide_altnames)

    date_option = prefsTop.get_widget("date_format")
    date_menu = GtkMenu()
    for index in range(0,len(_date_format_list)):
        item = GtkMenuItem(_date_format_list[index])
        item.set_data("i",index)
        item.set_data("o",pbox)
        item.connect("activate", on_format_toggled)
        item.show()
        date_menu.append(item)
    date_menu.set_active(Date.formatCode)
    date_option.set_menu(date_menu)

    date_entry = prefsTop.get_widget("date_entry_format")
    date_menu = GtkMenu()
    for index in range(0,len(_date_entry_list)):
        item = GtkMenuItem(_date_entry_list[index])
        item.set_data("i",index)
        item.set_data("o",pbox)
        item.connect("activate", on_format_toggled)
        item.show()
        date_menu.append(item)
    date_menu.set_active(Date.entryCode)
    date_entry.set_menu(date_menu)

    name_option = prefsTop.get_widget("name_format")
    name_menu = GtkMenu()
    for index in range(0,len(_name_format_list)):
        name_tuple = _name_format_list[index]
        item = GtkMenuItem(name_tuple[0])
        item.set_data("i",index)
        item.set_data("o",pbox)
        item.connect("activate", on_format_toggled)
        item.show()
        name_menu.append(item)
    name_menu.set_active(_name_format)
    name_option.set_menu(name_menu)

    prefsTop.get_widget("resname").set_text(owner.getName())
    prefsTop.get_widget("resaddr").set_text(owner.getAddress())
    prefsTop.get_widget("rescity").set_text(owner.getCity())
    prefsTop.get_widget("resstate").set_text(owner.getState())
    prefsTop.get_widget("rescountry").set_text(owner.getCountry())
    prefsTop.get_widget("respostal").set_text(owner.getPostalCode())
    prefsTop.get_widget("resphone").set_text(owner.getPhone())
    prefsTop.get_widget("resemail").set_text(owner.getEmail())

    if ListColors.enable == None:
        ListColors.enable = 0

    cwidget = prefsTop.get_widget(ODDFGCOLOR)
    cwidget.set_i16(ListColors.oddfg[0],ListColors.oddfg[1],\
                    ListColors.oddfg[2],0xffff)

    cwidget = prefsTop.get_widget(ODDBGCOLOR)
    cwidget.set_i16(ListColors.oddbg[0],ListColors.oddbg[1],\
                    ListColors.oddbg[2],0xffff)

    cwidget = prefsTop.get_widget(EVENFGCOLOR)
    cwidget.set_i16(ListColors.evenfg[0],ListColors.evenfg[1],\
                    ListColors.evenfg[2],0xffff)

    cwidget = prefsTop.get_widget(EVENBGCOLOR)
    cwidget.set_i16(ListColors.evenbg[0],ListColors.evenbg[1],\
                    ListColors.evenbg[2],0xffff)

    prefsTop.get_widget("enableColors").set_active(ListColors.enable)
    prefsTop.get_widget(ODDFGCOLOR).set_sensitive(ListColors.enable)
    prefsTop.get_widget(ODDBGCOLOR).set_sensitive(ListColors.enable)
    prefsTop.get_widget(EVENBGCOLOR).set_sensitive(ListColors.enable)
    prefsTop.get_widget(EVENFGCOLOR).set_sensitive(ListColors.enable)
        
    pbox.set_modified(0)
    pbox.show()

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def get_config_color(name,defval):
    r = gnome.config.get_int("/gramps/color/" + name + ".r")
    g = gnome.config.get_int("/gramps/color/" + name + ".g")
    b = gnome.config.get_int("/gramps/color/" + name + ".b")
    if not r:
        return defval
    else:
        return (r,g,b)
    
#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def druid_cancel_clicked(obj,a):
    utils.destroy_passed_object(obj)



