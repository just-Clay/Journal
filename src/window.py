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
    italic_toggle=Gtk.Template.Child()
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
        self.header1 = self.buffer.create_tag("header1", scale=2.2, weight=Pango.Weight.SEMIBOLD)
        self.header2 = self.buffer.create_tag("header2", scale=2, weight=Pango.Weight.SEMIBOLD)
        self.header3 = self.buffer.create_tag("header3", scale=1.8, weight=Pango.Weight.SEMIBOLD)
        self.header4 = self.buffer.create_tag("header4", scale=1.6, weight=Pango.Weight.SEMIBOLD)
        self.header5 = self.buffer.create_tag("header5", scale=1.4, weight=Pango.Weight.SEMIBOLD)
        self.header6 = self.buffer.create_tag("header6", scale=1.2, weight=Pango.Weight.SEMIBOLD)
        self.updating_ui = False
        self.current_tags = {"bold": False, "italic": False, "header": 0}
        self.cursor_position = -1
        self.old_length = self.buffer.get_char_count()

        #Editor buttons
        self.bold_toggle.connect("toggled", lambda _: self.on_bold_toggled())
        self.italic_toggle.connect("toggled", lambda _: self.on_italic_toggled())
        self.header_selector.connect("notify::selected", lambda *_: self.on_header_selected())
        self.buffer.connect_after("insert-text", self.on_write)
        self.buffer.connect_after("delete-range", self.after_delete)
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
    def on_bold_toggled(self):
        #Stop if we are just updating ui
        if self.updating_ui:
            return
        #Was an area selected when the toggle happened?
        #If so, we are going to change the tags for that area based off of the
        #starting tag of the selected area. Then we are going to adjust the
        #current_tags and the toggle appropriately.
        if self.buffer.get_selection_bounds():
            start, end = self.buffer.get_selection_bounds()
            if self.bold not in start.get_tags():
                self.buffer.apply_tag(self.bold, start, end)
                self.current_tags["bold"] = True
                #Don't forget to update the button so it looks right
                self.updating_ui = True
                self.bold_toggle.set_active(True)
                self.updating_ui = False
            else:
                self.buffer.remove_tag(self.bold, start, end)
                self.current_tags["bold"] = False
                #Updating the button
                self.updating_ui = True
                self.bold_toggle.set_active(False)
                self.updating_ui = False
        #If no area was selected, we will just flip the toggle
        else:
            if self.current_tags["bold"]:
                self.current_tags["bold"] = False
            else:
                self.current_tags["bold"] = True

    def on_italic_toggled(self):
        if self.updating_ui:
            return
        #Was an area selected when the toggle happened?
        #If so, we are going to change the tags for that area based off of the
        #starting tag of the selected area. Then we are going to adjust the
        #current_tags and the toggle appropriately.
        if self.buffer.get_selection_bounds():
            start, end = self.buffer.get_selection_bounds()
            if self.italic not in start.get_tags():
                self.buffer.apply_tag(self.italic, start, end)
                self.current_tags["italic"] = True
                #Don't forget to update the button so it looks right
                self.updating_ui = True
                self.italic_toggle.set_active(True)
                self.updating_ui = False
            else:
                self.buffer.remove_tag(self.italic, start, end)
                self.current_tags["italic"] = False
                #Updating the button
                self.updating_ui = True
                self.italic_toggle.set_active(False)
                self.updating_ui = False
        #If no area was selected, we will just flip the toggle
        else:
            if self.current_tags["italic"]:
                self.current_tags["italic"] = False
            else:
                self.current_tags["italic"] = True

    def on_header_selected(self):
        if self.updating_ui:
            return

        styles = [self.header1, self.header2, self.header3, self.header4, self.header5, self.header6]
        style_num = self.header_selector.get_selected()
        self.current_tags["header"] = style_num

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
        if style_num != 0:
            self.buffer.apply_tag(styles[style_num - 1], start, end)

    #This fixes a funky header bug where you could get to different header tags
    #on the same line by making the different tags on seperate lines
    #and then merging them through deletion. We want to avoid this because
    #we will be saving the files as markdown, which cannot have header text and
    #non-header text in the same line.
    def after_delete(self, buffer, start_deletion, end_deletion):
        start = start_deletion.copy()
        end = end_deletion.copy()
        start.set_line_offset(0)
        if not end.ends_line():
            end.forward_to_line_end()

        applied_tags = start.get_tags()
        if self.bold in applied_tags:
            applied_tags.remove(self.bold)
        if self.italic in applied_tags:
            applied_tags.remove(self.italic)
        if applied_tags == []:
            styles = [self.header1, self.header2, self.header3, self.header4, self.header5, self.header6]
            for style in styles:
                self.buffer.remove_tag(style, start, end)
        else:
            styles = [self.header1, self.header2, self.header3, self.header4, self.header5, self.header6]
            for style in styles:
                self.buffer.remove_tag(style, start, end)
            self.buffer.apply_tag(applied_tags[0], start, end)

    def on_write(self, buffer, location, text, length):
        if "\n" in text:
            self.current_tags["header"] = 0
            self.updating_ui = True
            self.header_selector.set_selected(0)
            self.updating_ui = False

        end = location.copy()
        start = location.copy()
        start.backward_chars(len(text))

        if self.current_tags["bold"]:
            buffer.apply_tag(self.bold, start, end)

        if self.current_tags["italic"]:
            buffer.apply_tag(self.italic, start, end)

        if self.current_tags["header"] != 0:
            headers = [self.header1, self.header2, self.header3, self.header4, self.header5, self.header6]
            buffer.apply_tag(headers[self.current_tags["header"] - 1], start, end)

    #When it moves, update the tags
    #in current tags based on the surrounding tags at the new location. If there
    #is no letters to the left of the cursor, use the letters to the right, but
    #otherwise, base this off of the character to the left of where the cursor
    #has moved
    def on_cursor_moved(self, buffer, pspec):
        cursor_offset = buffer.get_property("cursor-position")
        character_count = self.buffer.get_char_count()

        if (cursor_offset - 1 != self.cursor_position or character_count - 1 != self.old_length) and character_count != 0:
            #We must have jumped or deleted something
            location = buffer.get_iter_at_offset(cursor_offset)
            target = location.copy()
            if not target.starts_line():
                target.backward_char()
            applied_tags = target.get_tags()
            read_tags = []
            for tag in applied_tags:
                read_tags.append(tag.get_property("name"))

            self.updating_ui = True

            if "bold" in read_tags:
                self.current_tags["bold"] = True
                self.bold_toggle.set_active(True)
                read_tags.remove("bold")
            else:
                self.current_tags["bold"] = False
                self.bold_toggle.set_active(False)
            if "italic" in read_tags:
                self.current_tags["italic"] = True
                self.italic_toggle.set_active(True)
                read_tags.remove("italic")
            else:
                self.current_tags["italic"] = False
                self.italic_toggle.set_active(False)

            if read_tags == []:
                self.current_tags["header"] = 0
                self.header_selector.set_selected(0)
            else:
                header = read_tags[0]
                if header == "header1":
                    self.current_tags["header"] = 1
                    self.header_selector.set_selected(1)
                elif header == "header2":
                    self.current_tags["header"] = 2
                    self.header_selector.set_selected(2)
                elif header == "header3":
                    self.current_tags["header"] = 3
                    self.header_selector.set_selected(3)
                elif header == "header4":
                    self.current_tags["header"] = 4
                    self.header_selector.set_selected(4)
                elif header == "header5":
                    self.current_tags["header"] = 5
                    self.header_selector.set_selected(5)
                elif header == "header6":
                    self.current_tags["header"] = 6
                    self.header_selector.set_selected(6)


            self.updating_ui = False

        self.cursor_position = cursor_offset
        self.old_length = character_count

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
