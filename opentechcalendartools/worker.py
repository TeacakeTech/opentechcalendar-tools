import sqlite3

import opentechcalendartools.importers.eventbrite_organisation
import opentechcalendartools.importers.ical
from opentechcalendartools.settings import Settings


class Worker:

    def __init__(self, settings: Settings):
        self._settings: Settings = settings

    def get_group_ids_to_import(self) -> list:
        with sqlite3.connect(self._settings.SQLITE_DATABASE_FILENAME) as connection:
            res = connection.cursor().execute(
                "SELECT id FROM record_group WHERE field_import_type != '' AND field_import_type IS NOT NULL ORDER BY id ASC"
            )
            return [i[0] for i in res.fetchall()]

    def import_group(self, group_id):
        with sqlite3.connect(self._settings.SQLITE_DATABASE_FILENAME) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            res = cursor.execute("SELECT * FROM record_group WHERE id=?", [group_id])
            group = res.fetchone()
            if group["field_import_type"] == "ical":
                importer = opentechcalendartools.importers.ical.ImportICAL(
                    self._settings
                )
                importer.go(group)
            elif group["field_import_type"] == "eventbrite-organisation":
                importer = opentechcalendartools.importers.eventbrite_organisation.ImportEventbriteOrganisation(
                    self._settings
                )
                importer.go(group)
