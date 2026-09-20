# window.py
#
# Copyright 2026 Connor Gable
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw
from gi.repository import Gtk

@Gtk.Template(resource_path='/io/github/just_Clay/Journal/window.ui')
class JournalWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'JournalWindow'

#Stack view buttons
    stack = Gtk.Template.Child()
    calendar_button = Gtk.Template.Child()
    timeline_button = Gtk.Template.Child()
    on_this_day_button = Gtk.Template.Child()
    search_button = Gtk.Template.Child()


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.calendar_button.connect(
        "clicked", lambda _: self.stack.set_visible_child_name("calendar"))
        self.timeline_button.connect(
        "clicked", lambda _: self.stack.set_visible_child_name("timeline"))
        self.on_this_day_button.connect(
        "clicked", lambda _: self.stack.set_visible_child_name("on_this_day"))
        self.search_button.connect(
        "clicked", lambda _: self.stack.set_visible_child_name("editor"))
