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
        if self.updating_ui:
            return

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
        for style in self.styles:
            self.buffer.remove_tag(style, start, end)
        if applied_tags:
            self.buffer.apply_tag(applied_tags[0], start, end)

    #This function is ugly but I don't want to clean it up tbh
    def on_cursor_moved(self, buffer, pspec):
        cursor_offset = buffer.get_property("cursor-position")
        character_count = self.buffer.get_char_count()

        #Check if we jumped forward or moved backwards
        if cursor_offset != self.cursor_position and (cursor_offset - 1 != self.cursor_position or character_count - 1 != self.old_length) and character_count != 0:
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
                level = int(header[-1])
                self.current_tags["header"] = level
                self.header_selector.set_selected(level)


            self.updating_ui = False

        self.cursor_position = cursor_offset
        self.old_length = character_count

    def translate_buffer(self):
        def apply_closer(current_line, current_closer):
            if not current_closer:
                return current_line
            trailing_whitespace = ""
            while current_line and current_line[-1].isspace():
                trailing_whitespace = current_line[-1] + trailing_whitespace
                current_line = current_line[:-1]
            return current_line + current_closer + trailing_whitespace

        start_line = self.buffer.get_start_iter()
        end = self.buffer.get_end_iter()
        markdown = ""

        while not start_line.equal(end):
            end_line = start_line.copy()
            end_line.forward_line()

            line_tags = [tag.get_property("name") for tag in start_line.get_tags()]
            if "header1" in line_tags:
                markdown += "# "
            elif "header2" in line_tags:
                markdown += "## "
            elif "header3" in line_tags:
                markdown += "### "
            elif "header4" in line_tags:
                markdown += "#### "
            elif "header5" in line_tags:
                markdown += "##### "
            elif "header6" in line_tags:
                markdown += "###### "

            char = start_line.copy()
            bold_italic = False
            bold = False
            italic = False
            line = ""
            closer = ""
            while not char.equal(end_line):
                char_tags = [tag.get_property("name") for tag in char.get_tags()]
                if "bold" in char_tags and "italic" in char_tags:
                    if bold_italic:
                        line += char.get_char()
                    else:
                        bold = False
                        italic = False
                        bold_italic = True
                        line = apply_closer(line, closer)
                        closer = "***"
                        line += "***"
                        line += char.get_char()

                elif "bold" in char_tags:
                    if bold:
                        line += char.get_char()
                    else:
                        bold = True
                        italic = False
                        bold_italic = False
                        line = apply_closer(line, closer)
                        closer = "**"
                        line += "**"
                        line += char.get_char()

                elif "italic" in char_tags:
                    if italic:
                        line += char.get_char()
                    else:
                        bold = False
                        italic = True
                        bold_italic = False
                        line = apply_closer(line, closer)
                        closer = "*"
                        line += "*"
                        line += char.get_char()
                else:
                    if not bold and not italic and not bold_italic:
                        line += char.get_char()
                    else:
                        bold = False
                        italic = False
                        bold_italic = False
                        line = apply_closer(line, closer)
                        closer = ""
                        line += char.get_char()

                char.forward_char()

            line = apply_closer(line, closer)
            closer = ""
            markdown += line
            start_line = end_line

        return markdown

    def load_buffer(self, markdown_text):
        self.updating_ui = True
        self.buffer.set_text("")

        lines = markdown_text.split("\n")

        for line_idx, line in enumerate(lines):
            active_tags = []
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                if 1 <= level <= 6 and len(line) > level and line[level] == " ":
                    active_tags.append(self.styles[level - 1])
                    line = line[level + 1:]

            bold = False
            italic = False
            i = 0

            while i < len(line):
                if line[i:i+3] == "***":
                    bold = not bold
                    italic = not italic
                    i += 3
                elif line[i:i+2] == "**":
                    bold = not bold
                    i += 2
                elif line[i:i+1] == "*":
                    italic = not italic
                    i += 1
                else:
                    start = i
                    while i < len(line) and line[i] != "*":
                        i += 1
                    text_chunk = line[start:i]

                    chunk_tags = list(active_tags)
                    if bold:
                        chunk_tags.append(self.bold)
                    if italic:
                        chunk_tags.append(self.italic)

                    end_iter = self.buffer.get_end_iter()
                    start_offset = end_iter.get_offset()

                    self.buffer.insert(end_iter, text_chunk)

                    start_iter = self.buffer.get_iter_at_offset(start_offset)
                    new_end_iter = self.buffer.get_end_iter()

                    for tag in chunk_tags:
                        self.buffer.apply_tag(tag, start_iter, new_end_iter)

            if line_idx < len(lines) - 1:
                end_buffer = self.buffer.get_end_iter()
                self.buffer.insert(end_buffer, "\n")

        self.updating_ui = False
