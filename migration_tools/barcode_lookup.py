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

    def __init__(self, folio_client):
        """Init, setup"""
        self.folio_client = folio_client
        self.barcodes = [
            "000012725",
        ]

    def work(self):
        print("Starting....")
        for barcode in self.barcodes:
            q_path = f'/users?query=(barcode=="{barcode}")'
            response = self.folio_client.folio_get(q_path, "users")
            print(f"Found {len(response)} users for barcode {barcode} ")


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
    worker = Worker(folio_client)

    # Do work
    worker.work()


if __name__ == "__main__":
    """This is the Starting point for the script"""
    main()
