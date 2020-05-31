import argparse
import collections
import copy
import csv
import hashlib
import itertools
import json
import pathlib
import random
import time
import traceback
import uuid
import xml
import xml.etree.ElementTree as ET
from datetime import datetime as dt
from datetime import timedelta

import dateutil.parser
import requests
from folioclient.FolioClient import FolioClient


class Worker:
    """Class that is responsible for the acutal work"""

    def __init__(self, folio_client, loans):
        """Init, setup"""
        self.folio_client = folio_client
        self.loans = list(loans)
        print("Init done.")
        self.patron_item_combos = set()
        self.t0 = time.time()
        self.duplicate_loans = 0
        self.skipped_since_already_added = 0
        self.migration_report = {}
        self.processed_items = set()
        self.successful_items = set()
        self.failed = {}
        self.failed_and_not_dupe = {}

    def work(self):
        print("Starting....")
        # Iterate over every loan
        i = 0
        for loan in self.loans[500:]:
            if loan["item_id"] not in self.successful_items:
                try:
                    t0_fuction = time.time()
                    i += 1
                    loan_created = self.folio_client.check_out_by_barcode(
                        loan["item_barcode"],
                        loan["patron_barcode"],
                        dt.now(),
                        "83d474aa-ee99-4924-8704-a03e3c56e0d9",
                    )
                    # "extend" the loan date backwards in time in a randomized matter
                    if loan_created[0]:
                        # handle previously failed loans
                        if loan["item_id"] in self.failed:
                            print(
                                f"Loan suceeded but failed previously. Removing from failed {loan}"
                            )
                            # this loan har previously failed. It can now be removed from failures:
                            del self.failed[loan["item_id"]]

                        # extend loan
                        loan_to_extend = loan_created[1]
                        due_date = dateutil.parser.isoparse(loan["due_date"])
                        out_date = dateutil.parser.isoparse(loan["out_date"])
                        self.folio_client.extend_open_loan(loan_to_extend, due_date)
                        print(f"{timings(self.t0, t0_fuction, i)}")

                        self.successful_items.add(loan["item_id"])
                    # Loan Posting Failed
                    else:
                        # First failure
                        if loan["item_id"] not in self.failed:
                            print(f"Adding loan to failed {loan}")
                            self.failed[loan["item_id"]] = (loan_created, loan)
                        # Second Failure
                        else:
                            print(f"Loan already in failed {loan}")
                            self.failed_and_not_dupe[loan["item_id"]] = [
                                (loan_created, loan),
                                self.failed[loan["item_id"]],
                            ]
                            self.duplicate_loans += 1
                            del self.failed[loan["item_id"]]
                except Exception as ee:
                    print(f"Errror in row {i} {ee}")
                    raise ee
            else:
                print(f"loan already successfully processed {json.dumps(loan)}")
                self.skipped_since_already_added += 1
                self.duplicate_loans += 1
        # wrap up
        for k, v in self.failed.items():
            self.failed_and_not_dupe[k] = [v]
        # print(json.dumps(self.failed_and_not_dupe, sort_keys=True, indent=4))
        print("## Loan migration counters")
        print("Title | Number")
        print("--- | ---:")
        print(f"Duplicate rows in file | {self.duplicate_loans}")
        print(f"Skipped since already added | {self.skipped_since_already_added}")
        print(f"Successfully checked out items | {len(self.successful_items)}")
        print(f"Failed items/loans | {len(self.failed_and_not_dupe)}")
        print(f"Total Rows in file  | {i}")
        """for a in self.migration_report:
            print(f"# {a}")
            for b in self.migration_report[a]:
                print(b)"""

    def add_to_migration_report(self, header, messageString):
        if header not in self.migration_report:
            self.migration_report[header] = list()
        self.migration_report[header].append(messageString)


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


def timings(t0, t0func, num_objects):
    avg = num_objects / (time.time() - t0)
    elapsed = time.time() - t0
    elapsed_func = time.time() - t0func
    return f"Total objects: {num_objects}\tTotal elapsed: {elapsed:.2f}\tAverage per object: {avg:.2f}\tElapsed this time: {elapsed_func:.2f}"


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
