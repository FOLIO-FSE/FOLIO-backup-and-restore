import argparse
import csv
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
    def __init__(self, folio_client, args):
        self.folio_client = folio_client

    def work(self):
        print("going to work")


def main():
    args = parse_args()
    folio_client = FolioClient(
        args.okapi_url, args.tenant_id, args.username, args.password
    )
    worker = Worker(folio_client, args)
    worker.work()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file_path", help=("path to CSV file with UserId and Permission id")
    )
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


if __name__ == "__main__":
    main()
