# Copyright 2026 Connor Gable
# SPDX-License-Identifier: GPL-3.0-or-later

import pathlib, os, shutil

class StorageController:
    def __init__(self, journal_path, year, month, day):
        self.journal_path = journal_path
        self.journal = pathlib.Path(journal_path)
        self.year = year
        self.month = month
        self.day = day

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

    def add_attachment(self, file):
        file_name = file.get_basename()
        new_path = f"{self.journal_path}/{self.year}/{self.month}/{self.day}/{file_name}"
        shutil.copy(file.get_path(),(new_path))

    def add_dropped_attachments(self, files):
        for file in files:
            self.add_attachment(file)

    def delete(self, file_path):
        file_path.unlink()

    def fetch_attachments(self):
        file_list = []
        attachments_path = pathlib.Path(f"{self.journal_path}/{self.year}/{self.month}/{self.day}")
        for file in attachments_path.iterdir():
            file_list.append(file)
        return file_list
        
