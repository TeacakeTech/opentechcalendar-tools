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
                    group,
                    self._download_file_to_temp(group["field_import_url"]),
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
        self, group, ical_filename, group_country=None, group_place=None
    ):
        os.makedirs(os.path.join(self._data_dir, "event", group["id"]), exist_ok=True)
        with open(ical_filename) as fp:
            calendar = icalendar.Calendar.from_ical(fp.read())
            for event in calendar.events:
                start = event.get("DTSTART")
                end = event.get("DTEND")
                if end.dt.timestamp() > datetime.datetime.now().timestamp():
                    # Create event data with various fields
                    event_data = {
                        "title": str(event.get("SUMMARY")),
                        "group": group["id"],
                        "timezone": group["field_timezone"] or "UTC",
                        "start_at": str(start.dt),
                        "end_at": str(end.dt),
                        "url": str(event.get("URL")),
                        "cancelled": (event.get("STATUS") == "CANCELLED"),
                        "imported": True,
                        "community_participation": {
                            "at_event": None,
                            "at_event_audience_text": None,
                            "at_event_audience_audio": None,
                        },
                    }
                    if group["field_country"]:
                        event_data["country"] = group["field_country"]
                    if group["field_place"]:
                        event_data["place"] = group["field_place"]
                    if group["field_code_of_conduct_url"]:
                        event_data["code_of_conduct_url"] = group[
                            "field_code_of_conduct_url"
                        ]
                    # In-person events
                    if group["field_in_person"] == "all":
                        event_data["in_person"] = "yes"
                    elif group["field_in_person"] == "none":
                        event_data["in_person"] = "no"
                    # Community Participation: Interact with event?
                    if group["field_community_participation_at_event"] == "all":
                        event_data["community_participation"]["at_event"] = "yes"
                    elif group["field_community_participation_at_event"] == "none":
                        event_data["community_participation"]["at_event"] = "no"
                    # Community Participation: Interact with other audience members at the event via text?
                    if (
                        group["field_community_participation_at_event_audience_text"]
                        == "all"
                    ):
                        event_data["community_participation"][
                            "at_event_audience_text"
                        ] = "yes"
                    elif (
                        group["field_community_participation_at_event_audience_text"]
                        == "none"
                    ):
                        event_data["community_participation"][
                            "at_event_audience_text"
                        ] = "no"
                    # Community Participation: Interact with other audience members at the event via audio?
                    if (
                        group["field_community_participation_at_event_audience_audio"]
                        == "all"
                    ):
                        event_data["community_participation"][
                            "at_event_audience_audio"
                        ] = "yes"
                    elif (
                        group["field_community_participation_at_event_audience_audio"]
                        == "none"
                    ):
                        event_data["community_participation"][
                            "at_event_audience_audio"
                        ] = "no"
                    # Id
                    id = event.get("UID").split("@").pop(0)
                    # filename
                    filename = os.path.join(
                        self._data_dir, "event", group["id"], id + ".md"
                    )
                    # Finally write data
                    with open(filename, "w") as fp:
                        fp.write("---\n")
                        fp.write(yaml.dump(event_data))
                        fp.write("---\n\n\n")
                        fp.write(event.get("DESCRIPTION"))
                        fp.write("\n")
