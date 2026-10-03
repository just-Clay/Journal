# Copyright 2026 Connor Gable
# SPDX-License-Identifier: GPL-3.0-or-later

import pathlib, os, shutil

class StorageController:
    def __init__(self, journal_path, app_state):
        self.journal_path = journal_path
        self.journal = pathlib.Path(journal_path)
        self.app_state = app_state

    def index_days_with_entries(self):
        days_with_entries = {}
        if self.journal.exists() and self.journal.is_dir():
            for year in self.journal.iterdir():
                months_in_year = {}
                for month in year.iterdir():
                    days_in_month = []
                    for day in month.iterdir():
                        days_in_month.append(int(os.path.basename(day)))
                    months_in_year[int(os.path.basename(month))] = days_in_month
                days_with_entries[int(os.path.basename(year))] = months_in_year
        return days_with_entries

    def add_attachments(self, files):
        for file in files:
            file_name = file.get_basename()
            new_path = f"{self.journal_path}/{self.app_state.year}/{self.app_state.month}/{self.app_state.day}/{file_name}"
            shutil.copy(file.get_path(),(new_path))

    def delete(self, file_path):
        file_path.unlink()

    def fetch_attachments(self):
        file_list = []
        attachments_path = pathlib.Path(f"{self.journal_path}/{self.app_state.year}/{self.app_state.month}/{self.app_state.day}")
        for file in attachments_path.iterdir():
            if file.suffix != ".md":
                file_list.append(file)
        return file_list

    def fetch_entry(self):
        day_path = pathlib.Path(f"{self.journal_path}/{self.app_state.year}/{self.app_state.month}/{self.app_state.day}")
        file_path = day_path / f"{self.app_state.year}.{self.app_state.month}.{self.app_state.day}.md"
        if file_path.exists() and file_path.is_file():
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        return ""

    def open_new_entry(self):
        day_path = pathlib.Path(f"{self.journal_path}/{self.app_state.year}/{self.app_state.month}/{self.app_state.day}")
        day_path.mkdir(parents=True, exist_ok=True)

    def save_entry(self, markdown_text):
        if markdown_text == "":
            self.delete_entry_maybe_folder()
            return
        day_path = pathlib.Path(f"{self.journal_path}/{self.app_state.year}/{self.app_state.month}/{self.app_state.day}")
        day_path.mkdir(parents=True, exist_ok=True)
        file_path = day_path / f"{self.app_state.year}.{self.app_state.month}.{self.app_state.day}.md"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(markdown_text)

    def delete_entry_maybe_folder(self):
        day_path = pathlib.Path(f"{self.journal_path}/{self.app_state.year}/{self.app_state.month}/{self.app_state.day}")
        if day_path.exists() and day_path.is_dir():
            for file in day_path.iterdir():
                if file.suffix == ".md":
                    file.unlink()
            if len(list(day_path.iterdir())) == 0:
                day_path.rmdir()
