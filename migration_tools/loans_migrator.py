import argparse
import uuid
import hashlib
import itertools
import pathlib
import json
import csv
import random
import copy
import requests
import traceback
import dateutil.parser
import xml
from datetime import datetime as dt
import xml.etree.ElementTree as ET
import collections
from folioclient.FolioClient import FolioClient
from datetime import datetime, timedelta


class Worker:
    """Class that is responsible for the acutal work"""

    def __init__(self, folio_client, loans):
        """Init, setup"""
        self.folio_client = folio_client
        self.loans = list(loans)
        print("Init done.")

    def work(self):
        print("Starting....")
        # Iterate over every loan
        i = 0
        for loan in self.loans:
            try:
                i += 1
                loan_created = self.folio_client.check_out_by_barcode(
                    loan["item_barcode"],
                    loan["patron_barcode"],
                    datetime.now(),
                    "83d474aa-ee99-4924-8704-a03e3c56e0d9",
                )

                # "extend" the loan date backwards in time in a randomized matter
                if loan_created:
                    due_date = dateutil.parser.isoparse(loan["due_date"])
                    out_date = dateutil.parser.isoparse(loan["out_date"])
                    print(
                        f" loan created: {loan_created} {out_date.isoformat()} - {due_date.isoformat()}"
                    )
                    self.folio_client.extend_open_loan(loan_created, due_date)
            except Exception as ee:
                print(f"Errror in row {i} {ee}")
                raise ee


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
    # CSV parse the file
    csv.register_dialect("tsv", delimiter="\t")
    with open(args.from_path) as loans_file:
        loans = csv.DictReader(loans_file, dialect="tsv")

        # Initiate Worker
        worker = Worker(folio_client, loans)

        # Do work
        worker.work()


if __name__ == "__main__":
    """This is the Starting point for the script"""
    main()
