import argparse

from opentechcalendartools.settings import Settings

from .worker import Worker


def main():

    # First we process the data files into a SQLite database for us to use
    settings = Settings()
    if not settings.SQLITE_DATABASE_FILENAME:
        raise Exception(
            "Must specify OPEN_TECH_CALENDAR_TOOLS_SQLITE_DATABASE_FILENAME env var"
        )
        # TODO better would be to open a tempfile ourselves instead, and build it

    # Now check options ...
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="subparser_name")

    subparsers.add_parser("listgroupstoimport")

    import_group_parser = subparsers.add_parser("importgroup")
    import_group_parser.add_argument("group_id")

    args = parser.parse_args()

    worker = Worker(settings)

    if args.subparser_name == "listgroupstoimport":
        # List groups to import
        for group_id in worker.get_group_ids_to_import():
            print(group_id)

    elif args.subparser_name == "importgroup":
        # Import Group
        worker.import_group(args.group_id)
