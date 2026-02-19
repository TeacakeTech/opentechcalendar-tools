import datetime
import os
import zoneinfo

import icalendar
import yaml

from .base import ImportBase


class ImportICAL(ImportBase):

    def go(self, group: dict):
        os.makedirs(
            os.path.join(self._settings.DATA_DIRECTORY, "event", group["id"]),
            exist_ok=True,
        )
        with open(self._download_file_to_temp(group["field_import_url"])) as fp:
            calendar = icalendar.Calendar.from_ical(fp.read())
            for event in calendar.events:  # type: ignore
                timezone_name = group["field_timezone"] or "UTC"
                start_datetime = event.get("DTSTART").dt
                end_datetime = event.get("DTEND").dt
                if isinstance(start_datetime, datetime.datetime):
                    pass
                elif isinstance(start_datetime, datetime.date):
                    start_datetime = datetime.datetime(
                        start_datetime.year,
                        start_datetime.month,
                        start_datetime.day,
                        0,
                        0,
                        0,
                        tzinfo=zoneinfo.ZoneInfo(timezone_name),
                    )
                else:
                    raise Exception(
                        "Start not in the format we expect {}".format(start_datetime)
                    )
                if isinstance(end_datetime, datetime.datetime):
                    pass
                elif isinstance(end_datetime, datetime.date):
                    end_datetime = datetime.datetime(
                        end_datetime.year,
                        end_datetime.month,
                        end_datetime.day,
                        23,
                        59,
                        59,
                        tzinfo=zoneinfo.ZoneInfo(timezone_name),
                    )
                else:
                    raise Exception(
                        "End not in the format we expect {}".format(end_datetime)
                    )
                if self._should_import_event(
                    group,
                    str(event.get("SUMMARY")),
                    str(event.get("DESCRIPTION")),
                    end_datetime,
                ):
                    # Create event data with various fields
                    event_data = {
                        "title": str(event.get("SUMMARY")),
                        "group": group["id"],
                        "timezone": timezone_name,
                        "start_at": str(start_datetime),
                        "end_at": str(end_datetime),
                        "url": str(event.get("URL", "")) or group["field_url"],
                        "cancelled": (event.get("STATUS") == "CANCELLED"),
                        "imported": True,
                        "community_participation": {
                            "at_event": "unknown",
                            "at_event_audience_text": "unknown",
                            "at_event_audience_audio": "unknown",
                        },
                        "in_person": "unknown",
                    }
                    # Add data from group
                    self._update_event_with_group_data(event_data, group)
                    # Id
                    id = event.get("UID").split("@").pop(0)
                    # filename
                    filename = os.path.join(
                        self._settings.DATA_DIRECTORY, "event", group["id"], id + ".md"
                    )
                    # Finally write data
                    with open(filename, "w") as fp:
                        fp.write("---\n")
                        fp.write(yaml.dump(event_data))
                        fp.write("---\n\n\n")
                        fp.write(event.get("DESCRIPTION"))
                        fp.write("\n")
