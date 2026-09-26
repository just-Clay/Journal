# main.py
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

import sys
import gi
import os

from gettext import gettext as _

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw, Gdk
from .window import JournalWindow

class JournalApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='io.github.just_Clay.Journal',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
                         resource_base_path='/io/github/just_Clay/Journal')
        self.create_action('quit', lambda *_: self.quit(), ['<control>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)

        #Shortcuts
        self.set_accels_for_action("win.toggle-bold", ["<primary>b"])
        self.set_accels_for_action("win.toggle-italic", ["<primary>i"])

        #Settings
        self.settings = Gio.Settings.new('io.github.just_Clay.Journal')

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b""".today-border {outline: 2px solid @accent_color; outline-offset: 2px;}""")
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        win = self.props.active_window
        if not win:
            win = JournalWindow(application=self)
        win.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(application_name='Journal',
            application_icon='io.github.just_Clay.Journal',
            developer_name='Connor Gable',
            version='0.1.0',
            # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
            translator_credits = _('translator-credits'),
            developers=['Connor Gable'],
            copyright='© 2026 Connor Gable')
        about.present(self.props.active_window)


    def on_preferences_action(self, widget, _):
        builder = Gtk.Builder()
        builder.add_from_resource("/io/github/just_Clay/Journal/preferences.ui")

        prefs_window = builder.get_object("preferences_window")
        prefs_window.set_transient_for(self.get_active_window())

        file_location_label = builder.get_object("folder_location_title")
        file_location_label.set_subtitle(os.path.basename(self.settings.get_string("journal-location")))

        file_picker_btn = builder.get_object("file_picker")
        file_picker_btn.connect("clicked", self.on_file_picker_clicked, prefs_window, file_location_label)

        prefs_window.present()

    def on_file_picker_clicked(self, button, parent_window, file_location_label):
        dialog = Gtk.FileDialog()
        dialog.set_title("Select Journal Folder")

        dialog.select_folder(parent_window, None, self.on_folder_selected, file_location_label)

    def on_folder_selected(self, dialog, result, file_location_label):
        folder = dialog.select_folder_finish(result)
        if folder:
            folder_path = folder.get_path()
            self.settings.set_string("journal-location", folder_path)
            file_location_label.set_subtitle(os.path.basename(self.settings.get_string("journal-location")))

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

def main(version):
    """The application's entry point."""
    app = JournalApplication()
    return app.run(sys.argv)
