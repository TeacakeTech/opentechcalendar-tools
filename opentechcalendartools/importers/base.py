import datetime
import os
import sqlite3
import tempfile

from opentechcalendartools.settings import Settings


class ImportBase:

    def __init__(self, settings: Settings):
        self._settings: Settings = settings

    def _download_file_to_temp(self, url) -> str:
        r = self._settings.REQUESTS_SESSION.get(
            url,
            headers={"User-Agent": self._settings.USER_AGENT},
        )
        r.raise_for_status()
        new_filename_dets = tempfile.mkstemp(
            suffix="opentechcalendartools_",
        )
        os.write(new_filename_dets[0], r.content)
        os.close(new_filename_dets[0])
        return new_filename_dets[1]

    def _update_event_with_group_data(self, event_data: dict, group: dict):
        if group["field_country"]:
            event_data["country"] = group["field_country"]
        if group["field_place"]:
            event_data["place"] = group["field_place"]
        if group["field_code_of_conduct_url"]:
            event_data["code_of_conduct_url"] = group["field_code_of_conduct_url"]
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
        if group["field_community_participation_at_event_audience_text"] == "all":
            event_data["community_participation"]["at_event_audience_text"] = "yes"
        elif group["field_community_participation_at_event_audience_text"] == "none":
            event_data["community_participation"]["at_event_audience_text"] = "no"
        # Community Participation: Interact with other audience members at the event via audio?
        if group["field_community_participation_at_event_audience_audio"] == "all":
            event_data["community_participation"]["at_event_audience_audio"] = "yes"
        elif group["field_community_participation_at_event_audience_audio"] == "none":
            event_data["community_participation"]["at_event_audience_audio"] = "no"

    def _should_import_event(
        self, group: dict, title: str, description: str, end: datetime.datetime
    ) -> bool:
        # Has event passed?
        if end.timestamp() < datetime.datetime.now().timestamp():
            return False

        with sqlite3.connect(self._settings.SQLITE_DATABASE_FILENAME) as connection:
            # Check Excludes
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            for row in cursor.execute(
                "SELECT * FROM record_group___field_import_exclude WHERE record_id=?",
                [group["id"]],
            ):
                if row["value"] in title or row["value"] in description:
                    return False

            # Check includes
            any_includes = False
            for row in cursor.execute(
                "SELECT * FROM record_group___field_import_include WHERE record_id=?",
                [group["id"]],
            ):
                if row["value"] in title or row["value"] in description:
                    return True
                any_includes = True
            # If there were include values set but none of them matched then ...
            if any_includes:
                return False

        # Ok, have checked the excludes and there were no includes to check, so default to ....
        return True

    def go(self, group: dict):
        pass
