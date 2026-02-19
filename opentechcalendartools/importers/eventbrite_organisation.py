import datetime
import json
import os

import yaml
from bs4 import BeautifulSoup

from .base import ImportBase


class ImportEventbriteOrganisation(ImportBase):

    def go(self, group: dict):
        os.makedirs(
            os.path.join(self._settings.DATA_DIRECTORY, "event", group["id"]),
            exist_ok=True,
        )
        with open(self._download_file_to_temp(group["field_import_url"])) as fp:
            soup = BeautifulSoup(fp.read(), "html.parser")

            datas = [
                json.loads(s.string)  # type: ignore
                for s in soup.find_all("script", attrs={"type": "application/ld+json"})
            ]
            datas = [d for d in datas if isinstance(d.get("itemListElement"), list)]

            for event_jsonld_data in datas[0]["itemListElement"]:
                if event_jsonld_data["@type"] != "ListItem":
                    continue
                if event_jsonld_data["item"]["@type"] != "Event":
                    continue
                if event_jsonld_data["item"]["eventAttendanceMode"] not in [
                    "https://schema.org/OnlineEventAttendanceMode",
                    "https://schema.org/MixedEventAttendanceMode",
                ]:
                    continue
                timezone_name = group["field_timezone"] or "UTC"
                start_datetime = datetime.datetime.fromisoformat(
                    event_jsonld_data["item"]["startDate"]
                )
                end_datetime = datetime.datetime.fromisoformat(
                    event_jsonld_data["item"]["startDate"]
                )
                if self._should_import_event(
                    group,
                    event_jsonld_data["item"]["name"],
                    event_jsonld_data["item"]["description"],
                    end_datetime,
                ):

                    # Create event data with various fields
                    event_data = {
                        "title": event_jsonld_data["item"]["name"],
                        "group": group["id"],
                        "timezone": timezone_name,
                        "start_at": str(start_datetime),
                        "end_at": str(end_datetime),
                        "url": event_jsonld_data["item"]["url"],
                        "cancelled": False,  # TODO
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
                    # Overwrite group data with some extra data we know
                    if (
                        event_jsonld_data["item"]["eventAttendanceMode"]
                        == "https://schema.org/OnlineEventAttendanceMode"
                    ):
                        event_data["in_person"] = "no"
                    elif (
                        event_jsonld_data["item"]["eventAttendanceMode"]
                        == "https://schema.org/MixedEventAttendanceMode"
                    ):
                        event_data["in_person"] = "yes"
                    # Id
                    id = event_data["url"].split("/").pop(-1)
                    # filename
                    filename = os.path.join(
                        self._settings.DATA_DIRECTORY, "event", group["id"], id + ".md"
                    )
                    # Finally write data
                    with open(filename, "w") as fp:
                        fp.write("---\n")
                        fp.write(yaml.dump(event_data))
                        fp.write("---\n\n\n")
                        fp.write(event_jsonld_data["item"]["description"])
                        fp.write("\n")
