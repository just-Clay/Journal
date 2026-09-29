# Copyright 2026 Connor Gable
# SPDX-License-Identifier: GPL-3.0-or-later

import gi
gi.require_version('Pango', '1.0')
from gi.repository import Pango

class EditorController:
    def __init__(self, journal_entry, bold_toggle, italic_toggle, header_selector, stack):
        #Grab widgets
        self.journal_entry = journal_entry
        self.bold_toggle = bold_toggle
        self.italic_toggle = italic_toggle
        self.header_selector = header_selector
        self.stack = stack
        self.buffer = self.journal_entry.get_buffer()

        #Variables for cursor movement function
        self.old_length = self.buffer.get_char_count()
        self.cursor_position = -1

        #Set up our tags for editing.
        self.current_tags = {"bold": False, "italic": False, "header": 4}
        self.bold = self.buffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self.italic = self.buffer.create_tag("italic", style=Pango.Style.ITALIC)
        self.header1 = self.buffer.create_tag("header1", scale=1.85, weight=Pango.Weight.SEMIBOLD)
        self.header2 = self.buffer.create_tag("header2", scale=1.7, weight=Pango.Weight.SEMIBOLD)
        self.header3 = self.buffer.create_tag("header3", scale=1.55, weight=Pango.Weight.SEMIBOLD)
        self.header4 = self.buffer.create_tag("header4", scale=1.4, weight=Pango.Weight.SEMIBOLD)
        self.header5 = self.buffer.create_tag("header5", scale=1.25, weight=Pango.Weight.SEMIBOLD)
        self.header6 = self.buffer.create_tag("header6", scale=1.1, weight=Pango.Weight.SEMIBOLD)
        self.styles = [self.header1, self.header2, self.header3, self.header4, self.header5, self.header6]

        #Stops recursive calls and set initial header setting to 4
        self.updating_ui = True
        self.header_selector.set_selected(4)
        self.updating_ui = False

        #Scales up the editor font a little because I am blind
        self.journal_entry.add_css_class("editor-font")

        #Connects our widgets defined earlier to functions
        self.bold_toggle.connect("toggled", lambda _: self.on_bold_toggled())
        self.italic_toggle.connect("toggled", lambda _: self.on_italic_toggled())
        self.header_selector.connect("notify::selected", lambda *_: self.on_header_selected())
        self.buffer.connect_after("insert-text", self.on_write)
        self.buffer.connect_after("delete-range", self.after_delete)
        self.buffer.connect("notify::cursor-position", self.on_cursor_moved)

    def on_bold_toggled(self):
        if self.updating_ui:
            return

        if self.buffer.get_selection_bounds():
            start, end = self.buffer.get_selection_bounds()
            if self.bold not in start.get_tags():
                self.buffer.apply_tag(self.bold, start, end)
                self.current_tags["bold"] = True
            else:
                self.buffer.remove_tag(self.bold, start, end)
                self.current_tags["bold"] = False

        else:
            if self.current_tags["bold"]:
                self.current_tags["bold"] = False
            else:
                self.current_tags["bold"] = True

    def on_italic_toggled(self):
        if self.updating_ui:
            return

        if self.buffer.get_selection_bounds():
            start, end = self.buffer.get_selection_bounds()
            if self.italic not in start.get_tags():
                self.buffer.apply_tag(self.italic, start, end)
                self.current_tags["italic"] = True
            else:
                self.buffer.remove_tag(self.italic, start, end)
                self.current_tags["italic"] = False

        else:
            if self.current_tags["italic"]:
                self.current_tags["italic"] = False
            else:
                self.current_tags["italic"] = True

    def on_header_selected(self):
        if self.updating_ui:
            return

        style_num = self.header_selector.get_selected()
        self.current_tags["header"] = style_num

        if self.buffer.get_selection_bounds():
            start, end = self.buffer.get_selection_bounds()
        else:
            start = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            end = start.copy()

        start.set_line_offset(0)
        if not end.ends_line():
            end.forward_to_line_end()

        for style in self.styles:
            self.buffer.remove_tag(style, start, end)
        if style_num != 0:
            self.buffer.apply_tag(self.styles[style_num - 1], start, end)

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
            buffer.apply_tag(self.styles[self.current_tags["header"] - 1], start, end)

    #This functions only job is to make sure that the header tags only
    #exist on an entire line or no line at all.
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
            for style in self.styles:
                self.buffer.remove_tag(style, start, end)
        else:
            for style in self.styles:
                self.buffer.remove_tag(style, start, end)
            self.buffer.apply_tag(applied_tags[0], start, end)

    #This function is ugly but I don't want to clean it up tbh
    def on_cursor_moved(self, buffer, pspec):
        cursor_offset = buffer.get_property("cursor-position")
        character_count = self.buffer.get_char_count()

        #Check if we jumped forward or moved backwards
        if (cursor_offset - 1 != self.cursor_position or character_count - 1 != self.old_length) and character_count != 0:
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
