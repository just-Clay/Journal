# Copyright 2026 Connor Gable
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import date
from gi.repository import Adw, Gtk, Gdk, Gio, Pango
from .editor import EditorController
from .storage import StorageController
from .calendar import CalendarController

@Gtk.Template(resource_path='/io/github/just_Clay/Journal/window.ui')
class JournalWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'JournalWindow'

    """
    This class exists just to keep track of the current year, month, and day
    across our other python files. It is initialized later and passed in as
    an argument
    """
    class JournalState:
        def __init__(self):
            self.today = date.today()
            self.month = self.today.month
            self.year = self.today.year
            self.day = self.today.day

    #Main Navigation Buttons
    stack = Gtk.Template.Child()
    calendar_button = Gtk.Template.Child()
    timeline_button = Gtk.Template.Child()
    on_this_day_button = Gtk.Template.Child()
    search_button = Gtk.Template.Child()

    #Calendar widgets
    calendar_grid=Gtk.Template.Child()
    month_year=Gtk.Template.Child()
    prev_month=Gtk.Template.Child()
    next_month=Gtk.Template.Child()
    label_grid=Gtk.Template.Child()
    year_selector=Gtk.Template.Child()
    month_selector=Gtk.Template.Child()

    #Editor widgets
    journal_entry=Gtk.Template.Child()
    bold_toggle=Gtk.Template.Child()
    italic_toggle=Gtk.Template.Child()
    header_selector=Gtk.Template.Child()
    editor_date=Gtk.Template.Child()

    #Attachment widgets
    add_attachment=Gtk.Template.Child()
    attachment_pane=Gtk.Template.Child()
    attachment_view=Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        #This houses day, month, and year variables that we pass to controllers
        self.app_state = self.JournalState()

        #Navigation pane buttons
        self.calendar_button.connect(
        "clicked", lambda _: self.change_view("calendar"))
        self.timeline_button.connect(
        "clicked", lambda _: self.change_view("timeline"))
        self.on_this_day_button.connect(
        "clicked", lambda _: self.change_view("on_this_day"))
        self.search_button.connect(
        "clicked", lambda _: self.change_view("search"))

        #We need to save before the app closes
        self.connect("close-request", self.on_close_request)

        #Calendar view buttons
        self.prev_month.connect(
        "clicked", lambda _: self.calendar_controller.move_prev_month())
        self.next_month.connect(
        "clicked", lambda _: self.calendar_controller.move_next_month())

        #Editor shortcuts
        bold_action = Gio.SimpleAction.new("toggle-bold", None)
        bold_action.connect("activate", self.on_shortcut_bold)
        self.add_action(bold_action)
        italic_action = Gio.SimpleAction.new("toggle-italic", None)
        italic_action.connect("activate", self.on_shortcut_italic)
        self.add_action(italic_action)

        #Attachment widgets
        self.add_attachment.connect("clicked", lambda _: self.select_file())
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_files_dropped)
        self.add_controller(drop_target)

        #Set up storage controller
        app = self.get_application()
        self.journal_path = app.settings.get_string("journal-location")
        self.storage_controller = StorageController(self.journal_path, self.app_state)

        #Set up editor controller
        self.editor_controller = EditorController(self.journal_entry, self.bold_toggle,
        self.italic_toggle, self.header_selector, self.stack)

        #Set up calendar controller
        #The year selector needed a lot of help. I would like to simplify this if possible.
        #Some of this can probably be moved to xml, but I don't want to
        adj = self.year_selector.get_adjustment()
        adj.set_lower(1900.0)
        adj.set_upper(2100.0)
        adj.set_step_increment(1.0)
        self.year_selector.set_width_chars(5)

        self.calendar_controller = CalendarController(self.calendar_grid, self.month_year,
        self.prev_month, self.next_month, self.label_grid, self.year_selector, self.month_selector,
        self.storage_controller, self.on_day_selected, self.app_state)
        self.year_selector.connect("notify::value", self.calendar_controller.on_year_changed)
        self.calendar_controller.setup_calendar()
        self.calendar_controller.update_month_year()
        self.calendar_controller.make_calendar()

    def on_shortcut_bold(self, action, parameter):
        if self.stack.get_visible_child_name() == "editor":
            self.bold_toggle.set_active(not self.bold_toggle.get_active())

    def on_shortcut_italic(self, action, parameter):
        if self.stack.get_visible_child_name() == "editor":
            self.italic_toggle.set_active(not self.italic_toggle.get_active())

    #Day folder must first exist in order to add attachment
    def select_file(self):
        dialog = Gtk.FileDialog()
        dialog.set_title("Add Attachment")
        dialog.open_multiple(self, None, self.on_file_selected)

    def on_file_selected(self, dialog, result):
        files = dialog.open_multiple_finish(result)
        self.storage_controller.add_attachments(files)
        self.refresh_attachments()

    def on_files_dropped(self, drop_target, file_list, x, y):
        if self.stack.get_visible_child_name() != "editor" or not self.attachment_view.get_show_sidebar():
            return
        self.storage_controller.add_attachments(file_list)
        self.refresh_attachments()

    def open (self, file_path):
        gio_file = Gio.File.new_for_path(str(file_path))

        launcher = Gtk.FileLauncher.new(gio_file)
        launcher.set_always_ask(False)
        launcher.launch(self, None, None)

    def delete_file(self, file_path):
        self.storage_controller.delete(file_path)
        self.refresh_attachments()

    def on_day_selected(self, selected_day):
        self.stack.set_visible_child_name("editor")
        self.app_state.day = selected_day

        #Set the title
        suffix = "th"
        if selected_day//10 != 1:
            suffix_chooser = selected_day%10
            if 0 < suffix_chooser < 4:
                suffixes ={1:"st", 2:"nd", 3:"rd"}
                suffix = suffixes[suffix_chooser]

        self.editor_date.set_title(f"{self.calendar_controller.months[self.app_state.month - 1]} {self.app_state.day}{suffix}, {self.app_state.year}")

        self.storage_controller.open_new_entry()

        markdown_text = self.storage_controller.fetch_entry()
        self.editor_controller.load_buffer(markdown_text)

        self.refresh_attachments()

    def refresh_attachments(self):
        child = self.attachment_pane.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.attachment_pane.remove(child)
            child = next_child

        attachments = self.storage_controller.fetch_attachments()

        if attachments:
            self.attachment_view.set_show_sidebar(True)

        for file in attachments:
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            box.add_css_class("card")
            box.set_margin_start(10)
            box.set_margin_end(10)

            inner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            inner_box.set_margin_start(10)
            inner_box.set_margin_end(10)
            inner_box.set_margin_top(10)
            inner_box.set_margin_bottom(10)
            inner_box.set_spacing(10)

            label = Gtk.Label(label=file.name)
            label.set_hexpand(True)
            label.set_xalign(0)
            label.set_wrap(True)
            label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)

            open_button = Gtk.Button(icon_name="document-open-symbolic")
            open_button.set_valign(Gtk.Align.CENTER)
            open_button.set_halign(Gtk.Align.END)

            delete_button = Gtk.Button(icon_name="user-trash-symbolic")
            delete_button.set_valign(Gtk.Align.CENTER)
            delete_button.set_halign(Gtk.Align.END)
            delete_button.add_css_class("destructive-action")

            open_button.connect("clicked", lambda _, f=file: self.open(f))
            delete_button.connect("clicked", lambda _, f=file: self.delete_file(f))

            inner_box.append(label)
            inner_box.append(open_button)
            box.append(inner_box)
            inner_box.append(delete_button)
            self.attachment_pane.append(box)

    def change_view(self, view_name):
        if self.stack.get_visible_child_name() == "editor":
            self.save_and_clear_editor()

        self.stack.set_visible_child_name(view_name)

    def on_close_request(self, window):
        if self.stack.get_visible_child_name() == "editor":
            self.save_and_clear_editor()
        return False

    def save_and_clear_editor(self):
        markdown_text = self.editor_controller.translate_buffer()
        self.storage_controller.save_entry(markdown_text)
        self.editor_controller.buffer.set_text("")
