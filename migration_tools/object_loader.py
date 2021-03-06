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
import xml
import time
from datetime import datetime as dt
import xml.etree.ElementTree as ET
import collections
from folioclient.FolioClient import FolioClient


class Worker:
    """Class that is responsible for the acutal work"""

    def __init__(self, folio_client, objects_file, endpoint, skip):
        """Init, setup"""
        self.num_rows = 0
        self.skip = skip
        self.failed_posts = 0
        self.folio_client = folio_client
        self.objects_file = objects_file
        self.endpoint = endpoint
        self.t0 = time.time()
        print("Init done.")

    def work(self):
        print("Starting....")
        for _ in range(int(self.skip)):
            next(self.objects_file)
            self.num_rows += 1
        for row in self.objects_file:
            t0_fuction = time.time()
            self.num_rows += 1
            try:
                url = f"{self.folio_client.okapi_url}{self.endpoint}"
                req = requests.post(
                    url, headers=self.folio_client.okapi_headers, data=row
                )

                if req.status_code == 201:
                    print(f"{self.num_rows}\tHTTP {req.status_code}\tPOST {url}")
                elif req.status_code == 422:
                    self.failed_posts += 0
                    print(
                        f"{self.num_rows}\tHTTP {req.status_code}\t"
                        f"{json.loads(req.text)['errors'][0]['message']}\tPOST {url}\t{row}"
                        f" {timings(self.t0, t0_fuction, self.num_rows)}"
                    )
                else:
                    print(
                        f"{self.num_rows}\tHTTP {req.status_code}\t{req.text}\tPOST {url}\t{row}"
                    )
            except Exception as ee:
                print(f"Errror in row {self.num_rows} {ee}")
                if self.num_rows < 10:
                    raise ee

        print(f"Done! {self.num_rows} rows in file. Failed: {self.failed_posts}")


def timings(t0, t0func, num_objects):
    avg = num_objects / (time.time() - t0)
    elapsed = time.time() - t0
    elapsed_func = num_objects / (time.time() - t0func)
    return f"Objects processed: {num_objects}\tTotal elapsed: {elapsed}\tAverage per object: {avg:.2f}\tElapsed this time: {elapsed_func:.2f}"


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
    parser.add_argument("datafile", help="path to file with objects")
    parser.add_argument("endpoint", help="endpoint to post to")
    parser.add_argument("skip", default=0, help="endpoint to post to")

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
    with open(args.datafile) as data_file:

        # Initiate Worker
        worker = Worker(folio_client, data_file, args.endpoint, args.skip)

        # Do work
        worker.work()


if __name__ == "__main__":
    """This is the Starting point for the script"""
    main()
