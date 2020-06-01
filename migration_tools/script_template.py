import json
import argparse
from folioclient.FolioClient import FolioClient


class Worker:
    """Class that is responsible for the acutal work"""

    def __init__(self, folio_client):
        print("Initializing worker")
        self.folio_client = folio_client

    def work(self):
        print("Starting....")


def parse_args():
    """Parse CLI Arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "okapi_url",
        help=(
            "url of your FOLIO OKAPI endpoint."
            "See settings->software version in FOLIO"
        ),
    )
    parser.add_argument(
        "tenant_id",
        help=("id of the FOLIO tenant. " "See settings->software version in FOLIO"),
    )
    parser.add_argument("username", help=("the api user"))
    parser.add_argument("password", help=("the api users password"))
    parser.add_argument("from_path", help="path to file holdings the loans")
    args = parser.parse_args()
    return args


def main():
    """Main Method. Used for bootstrapping. """
    # Parse CLI Arguments
    args = parse_args()
    # Connect to a FOLIO tenant
    folio_client = FolioClient(
        args.okapi_url, args.tenant_id, args.username, args.password
    )

    # Initiate Worker
    worker = Worker(folio_client)

    # Do work
    worker.work()


if __name__ == "__main__":
    """This is the Starting point for the script"""
    main()
