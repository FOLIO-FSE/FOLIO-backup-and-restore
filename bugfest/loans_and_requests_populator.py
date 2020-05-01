import argparse
import uuid
import hashlib
import itertools
import pathlib
import json
import random
import copy
import requests
import traceback
import xml
import xml.etree.ElementTree as ET
import collections
from folioclient.FolioClient import FolioClient
from faker import Faker
from datetime import datetime, timedelta


class Worker:
    """Class that is responsible for the acutal work"""

    def __init__(self, folio_client, args):
        """Init, setup"""
        self.folio_client = folio_client
        self.faker = Faker()
        self.items = set()
        self.loan_policies = {}
        self.create_requests = args.create_requests
        self.create_page_requests = args.create_page_requests
        print(
            f"Init. Interacting with tenant {args.tenant_id} as {args.username}  at {args.okapi_url}",
            flush=True,
        )
        self.patron_groups = folio_client.get_all_ids("/groups")
        print(f"Fetched {len(self.patron_groups)} patron groups")

        self.item_loan_types = folio_client.get_all_ids("/loan-types")
        print(f"Fetched {len(self.item_loan_types)} item loan types")

        self.item_material_types = folio_client.get_all_ids("/material-types")
        print(f"Fetched {len(self.item_material_types)} item material types")

        self.service_points = folio_client.get_all_ids(
            "/service-points", "?query=(pickupLocation==true)"
        )
        print(f"Fetched {len(self.service_points)} Service points")

        self.locations = folio_client.get_all_ids("/locations")
        print(f"Fetched {len(self.locations)} locations")

        self.item_seeds = list(
            itertools.product(
                self.item_material_types, self.item_loan_types, self.locations
            )
        )
        # Shuffle the list of combinations so that you can run multiple instances at the same time
        random.shuffle(self.item_seeds)
        print(
            f"Created randomized list of {len(self.item_seeds)} possible combinations"
        )
        print("Init done.")
        LOST ITEMS!

    def work(self):
        print("Starting....")
        # Iterate over every combination
        for seed in self.item_seeds:
            material_type_id = seed[0]
            loan_type_id = seed[1]
            location_id = seed[2]
            i_query = f'?query=(materialTypeId="{material_type_id}" and permanentLoanTypeId="{loan_type_id}" and effectiveLocationId="{location_id}" and status.name=="Available")'
            # iterate over every patron group
            for patron_group_id in self.patron_groups:

                # get random Items from FOLIO based on the combination of parameters
                items = self.folio_client.get_random_objects(
                    "/item-storage/items", 10, query=i_query
                )

                # Get patrons from the current patron group
                p_query = f'query=(patronGroup=="{patron_group_id}" and active==true)'
                patrons = self.folio_client.get_random_objects("/users", 10, p_query)

                # tie a patron to an item
                item_patrons = zip(items, patrons)

                for item_patron in item_patrons:

                    # make sure we have barcodes
                    if "barcode" in item_patron[1] and "barcode" in item_patron[0]:

                        # pick a random service point
                        service_point_id = random.choice(self.service_points)

                        # 5 out of 6 items are checked out if argument -p was given
                        if random.randint(0, 5) > 0 or not self.create_page_requests:
                            # check out the item
                            loan = self.folio_client.check_out_by_barcode(
                                item_patron[0]["barcode"],
                                item_patron[1]["barcode"],
                                datetime.now(),
                                service_point_id,
                            )

                            # "extend" the loan date backwards in time in a randomized matter
                            if loan:
                                extension_date = self.faker.date_time_between(
                                    start_date="-1y", end_date="now"
                                )
                                self.folio_client.extend_open_loan(loan, extension_date)

                        # 1 out of 6 items are paged if argument -p was given
                        else:
                            print("create page request", flush=True)
                            self.folio_client.create_request(
                                "Page",
                                item_patron[1],
                                item_patron[0],
                                service_point_id,
                            )

                        # TODO: speed up this thingy. Fetching users is slow
                        # Create requests for the loan or page. If -r was given
                        if self.create_requests:
                            for b in random.sample(range(30), random.randint(1, 4)):
                                # pick random patron
                                new_patron = next(
                                    iter(
                                        self.folio_client.get_random_objects(
                                            "/users", 1, p_query
                                        )
                                    )
                                )
                                # request the item
                                self.folio_client.create_request(
                                    random.choice(["Hold", "Recall"]),
                                    new_patron,
                                    item_patron[0],
                                    service_point_id,
                                )


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
    parser.add_argument(
        "-create_requests",
        "-r",
        help=("Add requests to created loan or page"),
        action="store_true",
    )
    parser.add_argument(
        "-create_page_requests",
        "-p",
        help=("Create page requests as well as loans"),
        action="store_true",
    )
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
    
    # Iniiate Worker
    worker = Worker(folio_client, args)
    
    # Do work
    worker.work()


if __name__ == "__main__":
    """This is the Starting point for the script"""
    main()
