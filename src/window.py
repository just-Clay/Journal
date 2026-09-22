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

import calendar
from datetime import date
from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import Pango

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
    italics_toggle=Gtk.Template.Child()
    header_selector=Gtk.Template.Child()


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

        #Prepare buffer and tags
        self.buffer = self.journal_entry.get_buffer()
        self.bold = self.buffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self.italic = self.buffer.create_tag("italic", style=Pango.Style.ITALIC)
        self.header1 = self.buffer.create_tag("header1", scale=1.9, weight=Pango.Weight.SEMIBOLD)
        self.header2 = self.buffer.create_tag("header2", scale=1.7, weight=Pango.Weight.SEMIBOLD)
        self.header3 = self.buffer.create_tag("header3", scale=1.5, weight=Pango.Weight.SEMIBOLD)
        self.header4 = self.buffer.create_tag("header4", scale=1.4, weight=Pango.Weight.SEMIBOLD)
        self.header5 = self.buffer.create_tag("header5", scale=1.3, weight=Pango.Weight.SEMIBOLD)
        self.header6 = self.buffer.create_tag("header6", scale=1.1, weight=Pango.Weight.SEMIBOLD)
        self.is_updating_ui = False

        #Editor buttons
        self.bold_toggle.connect("toggled", lambda _: self.on_bold_toggled())
        self.italics_toggle.connect("toggled", lambda _: self.on_italic_toggled())
        self.header_selector.connect("notify::selected", lambda *_: self.on_header_selected())
        self.buffer.connect("notify::cursor-position", self.on_cursor_moved)

        #Making helpful variables for the calendar view
        self.today = date.today()
        self.month = self.today.month
        self.year = self.today.year
        self.day = self.today.day

        self.month_buttons = []
        self.day_buttons = []

        self.setup_calendar()
        self.update_month_year()
        self.make_calendar()


    #Editor view functions.
    #TODO remember to implement continuous tag application while typing for bold and italic
    def on_bold_toggled(self):
        is_active = self.bold_toggle.get_active()
        if self.buffer.get_selection_bounds():
            start, end = self.buffer.get_selection_bounds()
            if is_active:
                self.buffer.apply_tag(self.bold, start, end)
            else:
                self.buffer.remove_tag(self.bold, start, end)

    def on_italic_toggled(self):
        is_active = self.italics_toggle.get_active()
        if self.buffer.get_selection_bounds():
            start, end = self.buffer.get_selection_bounds()
            if is_active:
                self.buffer.apply_tag(self.italic, start, end)
            else:
                self.buffer.remove_tag(self.italic, start, end)

    def on_header_selected(self):
        if self.is_updating_ui:
            return
        styles = [self.header1, self.header2, self.header3, self.header4, self.header5, self.header6]
        style_num = self.header_selector.get_selected()

        #Select whole line
        if self.buffer.get_selection_bounds():
            start, end = self.buffer.get_selection_bounds()
        else:
            start = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            end = start.copy()
        start.set_line_offset(0)
        if not end.ends_line():
            end.forward_to_line_end()

        for style in styles:
            self.buffer.remove_tag(style, start, end)
        if style_num == 0:
            pass
        else:
            self.buffer.apply_tag(styles[style_num - 1], start, end)

    #Changes header button to match wherever cursor is
    def on_cursor_moved(self, *args):
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        checker = cursor.copy()
        if checker.ends_line() and not checker.starts_line():
            checker.backward_char()
        header_index = 0
        header_tags = [self.header1, self.header2, self.header3, self.header4, self.header5, self.header6]
        for i, tag in enumerate(header_tags):
            if checker.has_tag(tag):
                header_index = i + 1
                break
        if self.header_selector.get_selected() != header_index:
            self.is_updating_ui = True
            self.header_selector.set_selected(header_index)
            self.is_updating_ui = False


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
        for weekday_number, weekday in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
            day_label = Gtk.Label(label=weekday)
            self.label_grid.attach(day_label, weekday_number, 0, 1, 1)
        for month_number, month in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]):
            month_button = Gtk.Button(label=month)
            m_num = month_number + 1
            month_button.connect("clicked", lambda _, m=m_num: self.on_month_selected(m))
            self.month_buttons.append(month_button)
            self.month_selector.attach(month_button, month_number % 4, month_number // 4, 1, 1)

    #Update the calendar view when a new month is selected in the month year selector
    def on_month_selected(self, selected_month):
        self.month = selected_month
        self.update_month_year()
        self.make_calendar()

    #Update the calendar view when a new year is selected in the month year selector
    def on_year_changed(self, year_selector, parameter):
        self.year = int(year_selector.get_value())
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
        for weekNumber, week in enumerate(weeks):
            for day in week:
                if day == 0:
                    pass
                else:
                    day_button = Gtk.Button(label=str(day))
                    day_button.connect("clicked", lambda _, d=day: self.on_day_selected(d))
                    self.calendar_grid.attach(day_button, day-(7*weekNumber), weekNumber, 1, 1)

    def on_day_selected(self, selected_day):
        self.stack.set_visible_child_name("editor")
        print(selected_day)


    #Update calendar view when moving to the previous month
    def move_prev_month(self):
        if self.month > 1:
            self.month = self.month - 1
        else:
            self.year = self.year - 1
            self.month = 12
        self.update_month_year()
        self.make_calendar()

    #Update calendar view when moving to the next month
    def move_next_month(self):
        if self.month < 12:
            self.month = self.month + 1
        else:
            self.year = self.year + 1
            self.month = 1
        self.update_month_year()
        self.make_calendar()
