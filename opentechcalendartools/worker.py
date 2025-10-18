import datetime
import os
import sqlite3
import tempfile

import icalendar
import requests
import yaml


class Worker:

    def __init__(self, sqlite_database_filename):
        self._sqlite_database_filename = sqlite_database_filename
        self._data_dir = os.getcwd()

    def get_group_ids_to_import(self) -> list:
        with sqlite3.connect(self._sqlite_database_filename) as connection:
            res = connection.cursor().execute(
                "SELECT id FROM record_group WHERE field_import_type != '' AND field_import_type IS NOT NULL ORDER BY id ASC"
            )
            return [i[0] for i in res.fetchall()]

    def import_group(self, group_id):
        with sqlite3.connect(self._sqlite_database_filename) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            res = cursor.execute("SELECT * FROM record_group WHERE id=?", [group_id])
            group = res.fetchone()
            if group["field_import_type"] == "ical":
                self._import_group_type_ical(
                    group_id,
                    self._download_file_to_temp(group["field_import_url"]),
                    group_country=group["field_country"],
                    group_place=group["field_place"],
                )

    def _download_file_to_temp(self, url) -> str:
        r = requests.get(url)
        r.raise_for_status()
        new_filename_dets = tempfile.mkstemp(
            suffix="opentechcalendartools_",
        )
        os.write(new_filename_dets[0], r.content)
        os.close(new_filename_dets[0])
        return new_filename_dets[1]

    def _import_group_type_ical(
        self, group_id, ical_filename, group_country=None, group_place=None
    ):
        os.makedirs(os.path.join(self._data_dir, "event", group_id), exist_ok=True)
        with open(ical_filename) as fp:
            calendar = icalendar.Calendar.from_ical(fp.read())
            for event in calendar.events:
                start = event.get("DTSTART")
                end = event.get("DTEND")
                if end.dt.timestamp() > datetime.datetime.now().timestamp():
                    event_data = {
                        "title": str(event.get("SUMMARY")),
                        "group": group_id,
                        "start_at": str(start.dt),
                        "end_at": str(end.dt),
                        "url": str(event.get("URL")),
                        "cancelled": (event.get("STATUS") == "CANCELLED"),
                        "imported": True,
                    }
                    if group_country:
                        event_data["country"] = group_country
                    if group_place:
                        event_data["place"] = group_place
                    id = event.get("UID").split("@").pop(0)
                    filename = os.path.join(
                        self._data_dir, "event", group_id, id + ".md"
                    )
                    with open(filename, "w") as fp:
                        fp.write("---\n")
                        fp.write(yaml.dump(event_data))
                        fp.write("---\n\n\n")
                        fp.write(event.get("DESCRIPTION"))
