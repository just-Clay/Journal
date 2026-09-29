# Copyright 2026 Connor Gable
# SPDX-License-Identifier: GPL-3.0-or-later

import calendar, os, shutil
from datetime import date
from gi.repository import Adw, Gtk, Gdk, Gio
from .editor import EditorController
from .storage import StorageController

@Gtk.Template(resource_path='/io/github/just_Clay/Journal/window.ui')
class JournalWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'JournalWindow'

    #Stack view buttons
    stack = Gtk.Template.Child()
    calendar_button = Gtk.Template.Child()
    timeline_button = Gtk.Template.Child()
    on_this_day_button = Gtk.Template.Child()
    search_button = Gtk.Template.Child()

    #Calendar
    calendar_grid=Gtk.Template.Child()
    month_year=Gtk.Template.Child()
    prev_month=Gtk.Template.Child()
    next_month=Gtk.Template.Child()
    label_grid=Gtk.Template.Child()
    year_selector=Gtk.Template.Child()
    month_selector=Gtk.Template.Child()

    #Editor
    journal_entry=Gtk.Template.Child()
    bold_toggle=Gtk.Template.Child()
    italic_toggle=Gtk.Template.Child()
    header_selector=Gtk.Template.Child()
    editor_date=Gtk.Template.Child()

    #Attachments
    add_attachment=Gtk.Template.Child()
    attachment_pane=Gtk.Template.Child()
    attachment_view=Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        #Navigation pane buttons
        self.calendar_button.connect(
        "clicked", lambda _: self.stack.set_visible_child_name("calendar"))
        self.timeline_button.connect(
        "clicked", lambda _: self.stack.set_visible_child_name("timeline"))
        self.on_this_day_button.connect(
        "clicked", lambda _: self.stack.set_visible_child_name("on_this_day"))
        self.search_button.connect(
        "clicked", lambda _: self.stack.set_visible_child_name("search"))

        #Calendar view buttons
        self.prev_month.connect(
        "clicked", lambda _: self.move_prev_month())
        self.next_month.connect(
        "clicked", lambda _: self.move_next_month())

        #The year selector needed a lot of help. I would like to simplify this if possible.
        #Some of this can probably be moved to xml, but I don't want to
        adj = self.year_selector.get_adjustment()
        adj.set_lower(1900.0)
        adj.set_upper(2100.0)
        adj.set_step_increment(1.0)
        self.year_selector.set_width_chars(5)
        self.year_selector.connect("notify::value", self.on_year_changed)

        #Editor shortcuts
        bold_action = Gio.SimpleAction.new("toggle-bold", None)
        bold_action.connect("activate", self.on_shortcut_bold)
        self.add_action(bold_action)

        italic_action = Gio.SimpleAction.new("toggle-italic", None)
        italic_action.connect("activate", self.on_shortcut_italic)
        self.add_action(italic_action)

        #Attachment Buttons
        self.add_attachment.connect("clicked", lambda _: self.select_file())
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_files_dropped)
        self.add_controller(drop_target)

        #Making helpful variables for the calendar view
        self.months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.today = date.today()
        self.month = self.today.month
        self.year = self.today.year
        self.day = self.today.day
        self.days_with_entries = {}

        #Set up storage controller
        app = self.get_application()
        self.journal_path = app.settings.get_string("journal-location")
        self.storage_controller = StorageController(self.journal_path,
        self.year, self.month, self.day)

        self.month_buttons = []
        self.day_buttons = []

        self.setup_calendar()
        self.update_month_year()

        self.editor_controller = EditorController(self.journal_entry, self.bold_toggle,
        self.italic_toggle, self.header_selector, self.stack)

    def on_shortcut_bold(self, action, parameter):
        if self.stack.get_visible_child_name() == "editor":
            self.bold_toggle.set_active(not self.bold_toggle.get_active())

    def on_shortcut_italic(self, action, parameter):
        if self.stack.get_visible_child_name() == "editor":
            self.italic_toggle.set_active(not self.italic_toggle.get_active())

    #Update the month year selector to reflect correct month and year in calendar view
    def update_month_year(self):
        self.month_year.set_label(f"{calendar.month_name[self.month]} {self.year}")
        if int(self.year_selector.get_value()) != self.year:
            self.year_selector.set_value(self.year)
        for i, button in enumerate(self.month_buttons):
            month_number = i + 1
            if month_number == self.month:
                button.add_css_class("suggested-action")
            else:
                button.remove_css_class("suggested-action")

    #Make weekday row for calendar view and prepare month buttons in the month year selector
    def setup_calendar(self):
        for weekday_number, weekday in enumerate(self.days):
            day_label = Gtk.Label(label=weekday)
            self.label_grid.attach(day_label, weekday_number, 0, 1, 1)
        for month_number, month in enumerate(self.months):
            month_button = Gtk.Button(label=month)
            m_num = month_number + 1
            month_button.connect("clicked", lambda _, m=m_num: self.on_month_selected(m))
            self.month_buttons.append(month_button)
            self.month_selector.attach(month_button, month_number % 4, month_number // 4, 1, 1)

    #Update the calendar view when a new month is selected in the month year selector
    def on_month_selected(self, selected_month):
        self.month = selected_month
        self.storage_controller.month = selected_month
        self.update_month_year()
        self.make_calendar()

    #Update the calendar view when a new year is selected in the month year selector
    def on_year_changed(self, year_selector, parameter):
        self.year = int(year_selector.get_value())
        self.storage_controller.year = self.year
        self.update_month_year()
        self.make_calendar()

    #Clearing the calendar grid
    def clear_grid(self):
        child = self.calendar_grid.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.calendar_grid.remove(child)
            child = next_child

    #Fill in calendar grid
    def make_calendar(self):
        self.clear_grid()
        self.update_month_year()
        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(self.year, self.month)
        no_btn = Gtk.Button()

        days_with_entries = self.storage_controller.index_days_with_entries()

        for weekNumber, week in enumerate(weeks):
            for day in week:
                if day == 0:
                    pass
                else:
                    day_button = Gtk.Button(label=str(day))

                    if day == self.today.day and self.month == self.today.month and self.year == self.today.year:
                        day_button.add_css_class("today-border")

                    if self.year in days_with_entries:
                        if self.month in days_with_entries[self.year]:
                            if day in days_with_entries[self.year][self.month]:
                                day_button.add_css_class("suggested-action")

                    day_button.connect("clicked", lambda _, d=day: self.on_day_selected(d))
                    self.calendar_grid.attach(day_button, day-(7*weekNumber), weekNumber, 1, 1)

    def on_day_selected(self, selected_day):
        self.day = selected_day
        self.storage_controller.day = selected_day
        self.editor_date.set_title(f"{self.months[self.month - 1]} {self.day}th, {self.year}")
        self.stack.set_visible_child_name("editor")

        #The rest of this function is just handling attachments for the attachment pane
        child = self.attachment_pane.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.attachment_pane.remove(child)
            child = next_child

        attachments = self.storage_controller.fetch_attachments()

        if attachments:
            self.attachment_view.set_show_sidebar(True)
        else:
            self.attachment_view.set_show_sidebar(False)

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

            open_button = Gtk.Button(icon_name="document-open-symbolic")
            open_button.set_valign(Gtk.Align.CENTER)
            open_button.set_halign(Gtk.Align.END)

            delete_button = Gtk.Button(icon_name="user-trash-symbolic")
            delete_button.set_valign(Gtk.Align.CENTER)
            open_button.set_halign(Gtk.Align.END)
            delete_button.add_css_class("destructive-action")

            open_button.connect("clicked", lambda _, f=file: self.open(f))
            delete_button.connect("clicked", lambda _, f=file: self.delete_file(f))

            inner_box.append(label)
            inner_box.append(open_button)
            box.append(inner_box)
            inner_box.append(delete_button)
            self.attachment_pane.append(box)

    #Update calendar view when moving to the previous month
    def move_prev_month(self):
        if self.month > 1:
            self.month = self.month - 1
        else:
            self.year = self.year - 1
            self.month = 12
        self.storage_controller.month = self.month
        self.storage_controller.year = self.year
        self.update_month_year()
        self.make_calendar()

    #Update calendar view when moving to the next month
    def move_next_month(self):
        if self.month < 12:
            self.month = self.month + 1
        else:
            self.year = self.year + 1
            self.month = 1
        self.storage_controller.month = self.month
        self.storage_controller.year = self.year
        self.update_month_year()
        self.make_calendar()

    #Day folder must first exist in order to add attachment
    def select_file(self):
        dialog = Gtk.FileDialog()
        dialog.set_title("Add Attachment")
        dialog.open(self, None, self.on_file_selected)

    def on_file_selected(self, dialog, result):
        file = dialog.open_finish(result)
        self.storage_controller.add_attachment(file)
        self.on_day_selected(self.day)

    def on_files_dropped(self, drop_target, file_list, x, y):
        if self.stack.get_visible_child_name() != "editor" or not self.attachment_view.get_show_sidebar():
            return
        self.storage_controller.add_dropped_attachments(file_list)
        self.on_day_selected(self.day)

    def open (self, file_path):
        gio_file = Gio.File.new_for_path(str(file_path))

        launcher = Gtk.FileLauncher.new(gio_file)
        launcher.set_always_ask(False)
        launcher.launch(self, None, None)

    def delete_file(self, file_path):
        self.storage_controller.delete(file_path)
        self. on_day_selected(self.day)
