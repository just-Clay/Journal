# Copyright 2026 Connor Gable
# SPDX-License-Identifier: GPL-3.0-or-later

import calendar
from datetime import date
from gi.repository import Gtk

class CalendarController:
    def __init__(self, calendar_grid, month_year, prev_month, next_month,
    label_grid, year_selector, month_selector, storage_controller,
    on_day_selected, app_state):

        #We have a ton of buttons and widgets to import from window.py
        self.calendar_grid = calendar_grid
        self.month_year = month_year
        self.prev_month = prev_month
        self.next_month = next_month
        self.label_grid = label_grid
        self.year_selector = year_selector
        self.month_selector = month_selector
        self.storage_controller = storage_controller
        self.on_day_selected = on_day_selected

        self.months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.app_state = app_state
        self.today = date.today()
        self.days_with_entries = {}
        self.month_buttons = []
        self.day_buttons = []

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

    def update_month_year(self):
        self.month_year.set_label(f"{calendar.month_name[self.app_state.month]} {self.app_state.year}")
        if int(self.year_selector.get_value()) != self.app_state.year:
            self.year_selector.set_value(self.app_state.year)
        for i, button in enumerate(self.month_buttons):
            month_number = i + 1
            if month_number == self.app_state.month:
                button.add_css_class("suggested-action")
            else:
                button.remove_css_class("suggested-action")

    def on_month_selected(self, selected_month):
        self.app_state.month = selected_month
        self.update_month_year()
        self.make_calendar()

        #Update the calendar view when a new year is selected in the month year selector
    def on_year_changed(self, year_selector, parameter):
        self.app_state.year = int(year_selector.get_value())
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
        weeks = cal.monthdayscalendar(self.app_state.year, self.app_state.month)
        no_btn = Gtk.Button()

        days_with_entries = self.storage_controller.index_days_with_entries()

        for weekNumber, week in enumerate(weeks):
            for day in week:
                if day == 0:
                    pass
                else:
                    day_button = Gtk.Button(label=str(day))

                    if day == self.today.day and self.app_state.month == self.today.month and self.app_state.year == self.today.year:
                        day_button.add_css_class("today-border")

                    if self.app_state.year in days_with_entries:
                        if self.app_state.month in days_with_entries[self.app_state.year]:
                            if day in days_with_entries[self.app_state.year][self.app_state.month]:
                                day_button.add_css_class("suggested-action")

                    day_button.connect("clicked", lambda _, d=day: self.on_day_selected(d))
                    self.calendar_grid.attach(day_button, day-(7*weekNumber), weekNumber, 1, 1)

    #Update calendar view when moving to the previous month
    def move_prev_month(self):
        if self.app_state.month > 1:
            self.app_state.month = self.app_state.month - 1
        else:
            self.app_state.year = self.app_state.year - 1
            self.app_state.month = 12
        self.update_month_year()
        self.make_calendar()

    #Update calendar view when moving to the next month
    def move_next_month(self):
        if self.app_state.month < 12:
            self.app_state.month = self.app_state.month + 1
        else:
            self.app_state.year = self.app_state.year + 1
            self.app_state.month = 1
        self.update_month_year()
        self.make_calendar()
