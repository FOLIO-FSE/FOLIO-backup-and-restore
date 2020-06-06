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
from datetime import datetime
from datetime import timedelta

import dateutil.parser
import requests
from folioclient.FolioClient import FolioClient


class Worker:
    """Class that is responsible for the acutal work"""

    def __init__(self, folio_client, failed_items):
        """Init, setup"""
        self.folio_client = folio_client
        self.failed_items = failed_items
        self.unfound_patrons = set()
        self.expired_patrons = set()
        self.unfound_patron_barcodes = set()
        self.stats = {}

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
        self.checked_out_items = {}

    def work(self):
        print("Starting....")
        # Iterate over every loan
        i = 0
        for failed_loan in self.failed_items.values():
            # for failed_loan in failed_loans:
            # print(failed_loan)
            # print(failed_loan[0][2])
            fail_reason = failed_loan[0][2]
            if fail_reason == "Could not find user with matching barcode":
                add_stats(self.stats, f"Previous Fail reason: {fail_reason}")
                self.handle_patron_not_found(failed_loan)
            elif fail_reason == "Item is already checked out":
                add_stats(self.stats, f"Previous Fail reason: {fail_reason}")
                add_stats(self.stats, fail_reason)
            elif fail_reason == "Cannot check out item that already has an open loan":
                add_stats(self.stats, f"Previous Fail reason: {fail_reason}")
                add_stats(self.stats, fail_reason)
            elif fail_reason == "Cannot check out to inactive user":
                add_stats(self.stats, f"Previous Fail reason: {fail_reason}")
                self.handle_inactive_user(failed_loan)
            elif "Declared lost and cannot be checked" in fail_reason:
                add_stats(
                    self.stats,
                    f"Previous Fail reason: Declared lost and cannot be checked",
                )
                self.handle_declared_lost(failed_loan)
            elif fail_reason == "Item is not loanable":
                add_stats(self.stats, f"Previous Fail reason: {fail_reason}")
                self.handle_item_is_not_loanable(failed_loan)
            else:
                print(f"Undhandled fail reason: {fail_reason}")
                add_stats(self.stats, f"Undhandled fail reason: {fail_reason}")
                self.failed[failed_loan[1]["item_id"]] = failed_loan
            """if loan["item_id"] not in self.successful_items:
                try:
                    t0_fuction = time.time()
                    i += 1
                    
            else:
                print(f"loan already successfully processed {json.dumps(loan)}")
                self.skipped_since_already_added += 1
                self.duplicate_loans += 1"""
        # wrap up
        print("## Patrons ids not found")
        print(", ".join(sorted(self.unfound_patrons)))
        print("## Patron barcodes not found")
        print(", ".join(sorted(self.unfound_patron_barcodes)))
        print_dict_to_md_table(self.stats, "Measure", "Number")
        print("## Loan migration counters")
        print("Title | Number")
        print("--- | ---:")
        print(f"Duplicate rows in file | {self.duplicate_loans}")
        print(f"Skipped since already added | {self.skipped_since_already_added}")
        print(f"Successfully checked out items | {len(self.successful_items)}")
        print(f"Failed items/loans | {len(self.failed)}")
        for a in self.migration_report:
            print(f"# {a}")
            for b in self.migration_report[a]:
                print(b)
        print(json.dumps(self.failed, indent=4))

    def handle_declared_lost(self, fail):
        try:
            failed_loan = fail[1]
            self.failed[failed_loan["item_id"]] = fail
            q_path = (
                f'/item-storage/items?query=(barcode=="{failed_loan["item_barcode"]}")'
            )
            response = self.folio_client.folio_get(q_path, "items")
            print(f"Found {len(response)} items")
            item = response[0]
            print(f"Changing Status to Available for {json.dumps(failed_loan)}")
            item["status"]["name"] = "Available"
            put_item(self.folio_client, item)
            print(f"Checking out and extending {json.dumps(failed_loan)}")
            loan_created = self.checkout_and_extend(failed_loan)
            if not loan_created[0]:
                if loan_created[2] == "Item is not loanable":
                    print(f"checkout did not work. Trying override")
                    loan_res = self.override_check_out_by_barcode(
                        failed_loan["item_barcode"],
                        failed_loan["patron_barcode"],
                        failed_loan["due_date"],
                        "83d474aa-ee99-4924-8704-a03e3c56e0d9",
                    )
                    if not loan_res[0]:
                        raise Exception("Override failed")
                    loan_created = loan_res
                else:
                    raise Exception("Checkout failed")

            item["status"]["name"] = "Declared lost"
            print(f"Updating Item with status declared lost {json.dumps(failed_loan)}")
            put_item(self.folio_client, item)
            print("done")
        except Exception as ee:
            print(f"Declared lost {ee}")
            if loan_created:
                add_stats(self.stats, f"New Fail reason: {loan_created[2]}")
                fail[0] = loan_created
            self.failed[failed_loan["item_id"]] = fail
        finally:
            item["status"]["name"] = "Declared lost"
            print(
                f"Updating Item {item['id']} with status declared lost {json.dumps(failed_loan)}"
            )
            put_item(self.folio_client, item)
            print("done")

    def handle_item_is_not_loanable(self, fail):
        failed_loan = fail[1]
        print(f"Overriding {json.dumps(failed_loan)}")
        loan_res = []
        loan_res = self.override_check_out_by_barcode(
            failed_loan["item_barcode"],
            failed_loan["patron_barcode"],
            failed_loan["due_date"],
            "83d474aa-ee99-4924-8704-a03e3c56e0d9",
        )
        if loan_res and loan_res[0]:
            self.successful_items.add(failed_loan["id"])
        elif loan_res:
            add_stats(self.stats, f"New Fail reason: {loan_res[2]}")
            fail[0] = loan_res
            self.failed[failed_loan["item_id"]] = fail
        else:
            self.failed[failed_loan["item_id"]] = fail

    def handle_inactive_user(self, fail):
        failed_loan = fail[1]
        day_after_tomorrow = datetime.now() + timedelta(days=2)
        """Extend patron expiration date to tomorrow and try to check the thing out"""
        q_path = f'/users?query=(barcode=="{failed_loan["patron_barcode"]}")'
        response = self.folio_client.folio_get(q_path, "users")
        print(f"Found {len(response)} users")
        user = response[0]
        try:
            print(f"Extending user {failed_loan}")
            self.extend_user(user, day_after_tomorrow)
            print(f"Checking out and extending {failed_loan}")
            loan_created = self.checkout_and_extend(failed_loan)
            if not loan_created[0]:
                raise Exception("Checkout failed")
        except Exception as ee:
            print(print(f"Was: Inactive user! {ee} for  {failed_loan}"))
            if loan_created:
                add_stats(self.stats, f"New Fail reason: {loan_created[2]}")
                fail[0] = loan_created
            self.failed[failed_loan["item_id"]] = fail

    def handle_patron_not_found(self, fail):
        failed_loan = fail[1]
        loan_created = None
        try:
            q_path = (
                f'/item-storage/items?query=(barcode=="{failed_loan["item_barcode"]}")'
            )
            response = self.folio_client.folio_get(q_path, "items")
            print(f"Found {len(response)} items")
            item = response[0]
            if item["status"]["name"] == "Checked out":
                add_stats(self.stats, "Checked out, no idea to look for patron")
                raise Exception(f"Item is checked out already {failed_loan}")
            else:
                add_stats(self.stats, f'Item status: {item["status"]["name"]}')
            loan_created = self.checkout_and_extend(failed_loan)
            if not loan_created[0]:
                raise Exception("Checkout failed")
        except Exception as ee:
            if loan_created:
                add_stats(self.stats, f"New Fail reason: {loan_created[2]}")
                fail[0] = loan_created
                if loan_created[2] == "Could not find user with matching barcode":
                    """Keep track of not found users, so they could be looked up"""
                    p_number = failed_loan["patron_id"]
                    p_barcode = failed_loan["patron_barcode"]
                    if p_number not in self.unfound_patrons:
                        self.unfound_patrons.add(p_number)
                    if p_barcode not in self.unfound_patron_barcodes:
                        self.unfound_patron_barcodes.add(p_barcode)

                else:
                    print(f"ELSE: {loan_created[2]}")
                self.failed[failed_loan["item_id"]] = fail
            else:
                print(ee)
                traceback.print_exc()

    def extend_user(self, user, extension_date):
        if not user["expirationDate"].startswith("2020-06"):
            raise Exception(f"wrong expiration date {user['expirationDate']}")
        user_to_post = copy.deepcopy(user)
        del user_to_post["metadata"]
        user_to_post["active"] = True
        user_to_post["expirationDate"] = extension_date.isoformat()
        put_user(self.folio_client, user_to_post)
        print(f"PUT /users/{user['id']} {json.dumps(user_to_post)}")

    def checkout_and_extend(self, failed_loan):
        loan_created = self.folio_client.check_out_by_barcode(
            failed_loan["item_barcode"],
            failed_loan["patron_barcode"],
            datetime.now(),
            "83d474aa-ee99-4924-8704-a03e3c56e0d9",
        )
        # "extend" the loan date backwards in time in a randomized matter
        if loan_created[0]:
            # handle previously failed loans
            if failed_loan["item_id"] in self.failed:
                print(
                    f"Loan suceeded but failed previously. Removing from failed {failed_loan}"
                )
                # this loan har previously failed. It can now be removed from failures:
                del self.failed[failed_loan["item_id"]]

            # extend loan
            loan_to_extend = loan_created[1]
            due_date = dateutil.parser.isoparse(failed_loan["due_date"])
            out_date = dateutil.parser.isoparse(failed_loan["out_date"])
            extend_res = self.folio_client.extend_open_loan(
                loan_to_extend, due_date, out_date
            )
            if not extend_res:
                raise Exception(f"Failed to extend")
            return loan_created
        # Loan Posting Failed
        else:
            return loan_created

    def add_to_migration_report(self, header, messageString):
        if header not in self.migration_report:
            self.migration_report[header] = list()
        self.migration_report[header].append(messageString)

    def override_check_out_by_barcode(
        self, item_barcode, patron_barcode, due_date, service_point_id
    ):
        # TODO: add logging instead of print out
        try:
            data = {
                "itemBarcode": item_barcode,
                "userBarcode": patron_barcode,
                "dueDate": due_date,
                "servicePointId": service_point_id,
                "comment": "Overridden by migration process",
            }
            path = "/circulation/override-check-out-by-barcode"
            url = f"{self.folio_client.okapi_url}{path}"
            req = requests.post(
                url, headers=self.folio_client.okapi_headers, data=json.dumps(data)
            )
            if str(req.status_code) == "422":
                print(
                    f"{json.loads(req.text)['errors'][0]['message']}\t{json.dumps(data)}",
                    flush=True,
                )
                return (False, None, json.loads(req.text)["errors"][0]["message"])
            elif str(req.status_code) == "201":
                print(f"{req.status_code}\tPOST {url}", flush=True)
                return (True, json.loads(req.text), None)
            else:
                req.raise_for_status()
        except Exception as exception:
            print(f"\tPOST FAILED {url}\t{json.dumps(data)}", flush=True)
            traceback.print_exc()
            print(exception, flush=True)
            return (False, None, str(exception))


def add_stats(stats, a):
    if a not in stats:
        stats[a] = 1
    else:
        stats[a] += 1


def put_user(folio_client, user):
    """Fetches data from FOLIO and turns it into a json object as is"""
    url = f"{folio_client.okapi_url}/users/{user['id']}"
    print(url)
    req = requests.put(url, headers=folio_client.okapi_headers, data=json.dumps(user))
    print(req.status_code)
    req.raise_for_status()


def put_item(folio_client, item):
    """Fetches data from FOLIO and turns it into a json object as is"""
    url = f"{folio_client.okapi_url}/item-storage/items/{item['id']}"
    print(url)
    req = requests.put(url, headers=folio_client.okapi_headers, data=json.dumps(item))
    print(req.status_code)
    req.raise_for_status()


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


def print_dict_to_md_table(my_dict, h1, h2):
    # TODO: Move to interface or parent class
    d_sorted = {k: my_dict[k] for k in sorted(my_dict)}
    print(f"{h1} | {h2}")
    print("--- | ---:")
    for k, v in d_sorted.items():
        print(f"{k} | {v}")


def main():
    """Main Method. Used for bootstrapping. """
    # Parse CLI Arguments
    args = parse_args()
    # Connect to a FOLIO tenant
    folio_client = FolioClient(
        args.okapi_url, args.tenant_id, args.username, args.password
    )

    with open(args.from_path) as loans_file:
        loans = json.load(loans_file)
        # print(json.dumps(loans))
        print(f"{len(loans)} loans to process")
        # Initiate Worker
        worker = Worker(folio_client, loans)

        # Do work
        worker.work()


if __name__ == "__main__":
    """This is the Starting point for the script"""
    main()
