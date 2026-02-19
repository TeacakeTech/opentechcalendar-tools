import os

import requests
import requests_cache


class Settings:

    def __init__(self):

        self.USER_AGENT = (
            "Open Tech Calendar Tools https://opentechcalendar.co.uk/contact"
        )

        # TODO It's not really a directory, filename would be a better descriptor
        requests_cache_directory = os.getenv(
            "OPEN_TECH_CALENDAR_TOOLS_REQUEST_CACHE_DIRECTORY",
        )
        self.REQUESTS_SESSION = (
            requests_cache.CachedSession(requests_cache_directory)
            if requests_cache_directory
            else requests.Session()
        )
        self.DATA_DIRECTORY = os.getcwd()

        self.SQLITE_DATABASE_FILENAME = os.getenv(
            "OPEN_TECH_CALENDAR_TOOLS_SQLITE_DATABASE_FILENAME"
        )
