import json
import argparse


class Worker:
    """Class that is responsible for the acutal work"""

    def __init__(self, from_file, results_folder):
        print("Initializing worker")
        self.from_file = from_file
        self.results_folder = results_folder

    def work(self):
        print("Starting....")
        users = json.load(self.from_file)


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
    parser.add_argument("results_path", help="path to file holdings the loans")

    args = parser.parse_args()
    return args


def main():
    """Main Method. Used for bootstrapping. """
    # Parse CLI Arguments
    args = parse_args()
    # Connect to a FOLIO tenant

    # Initiate Worker
    worker = Worker(folio_client, args.from_path, args.results_path)

    # Do work
    worker.work()


if __name__ == "__main__":
    """This is the Starting point for the script"""
    main()
