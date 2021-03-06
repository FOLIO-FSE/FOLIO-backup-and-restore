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
from datetime import datetime as dt
import xml.etree.ElementTree as ET
import collections
from folioclient.FolioClient import FolioClient
import os
from os.path import isfile, join
from posix import listdir


class Worker:
    """Class that is responsible for the acutal work"""

    def __init__(
        self,
        folio_client,
        objects_file,
        batch_size,
        api_path,
        object_name,
        holdings_id_map,
    ):
        """Init, setup"""
        self.failed_ids = []
        self.api_path = api_path
        self.object_name = object_name
        self.failed_objects = []
        self.folio_client = folio_client
        self.batch_size = batch_size
        self.processed = 0
        self.processed_rows = 0
        self.objects_file = objects_file
        self.holdings_id_map = holdings_id_map

    def work(self):
        print("Starting....")
        batch = []
        files = [
            join(self.objects_file, f)
            for f in listdir(self.objects_file)
            if isfile(join(self.objects_file, f))
        ]
        for file in files:
            print(file)
            with open(file) as objects_file:
                for row in objects_file:
                    try:
                        json_rec = json.loads(row.split("\t")[-1])
                        if json_rec["mfhdId"] not in self.holdings_id_map:
                            raise ValueError(
                                f'Holdings id {json_rec["mfhdId"]} not in map'
                            )
                        else:
                            json_rec["holdingsRecordId"] = self.holdings_id_map[
                                json_rec["mfhdId"]
                            ]
                            del json_rec["mfhdId"]
                        if "copyNumbers" in json_rec:
                            if any(json_rec["copyNumbers"]):
                                json_rec["copyNumber"] = json_rec["copyNumbers"][0]
                            del json_rec["copyNumbers"]
                        self.processed_rows += 1
                        batch.append(json_rec)
                        if len(batch) == int(self.batch_size):
                            self.post_batch(batch)
                            batch = []
                    except Exception as exception:
                        print(f"{exception} row failed", flush=True)
                        batch = []
                        traceback.print_exc()
        self.post_batch(batch)
        print(json.dumps(self.failed_objects), flush=True)
        print(json.dumps(self.failed_ids, indent=4), flush=True)

    def post_batch(self, batch, repost=False):
        response = self.do_post(batch)
        if response.status_code == 201:
            print(
                f"Posting successfull! {self.processed_rows} {response.elapsed.total_seconds()}s {len(batch)}",
                flush=True,
            )
        elif response.status_code == 422:
            print(f"{response.status_code}\t{response.text}")
            resp = json.loads(response.text)
            for error in resp["errors"]:
                self.failed_ids.append(error["parameters"][0]["value"])
            print(f"1 {len(batch)}")
            self.handle_failed_batch(batch)
            """if not repost:
                self.handle_failed_batch(batch)
            else:
                raise Exception(f"Reposting despite handling. {self.failed_ids}")"""
        elif response.status_code in [500, 413]:
            # Error handling is sparse. Need to identify failing records
            print(f"{response.status_code}\t{response.text}")
            if not len(batch) == 1:
                # split the batch in 2
                my_chunks = chunks(batch, 2)
                for chunk in my_chunks:
                    print(
                        f"split batch in {len(my_chunks)} "
                        f"chunks with {len(chunk)} objects. "
                        "posting chunk..."
                    )
                    self.post_batch(chunk)
            else:
                print(
                    f"Only one object left. Adding {batch[0]['id']} to failed_objects"
                )
                self.failed_objects = batch[0]
        else:
            raise Exception(f"ERROR! HTTP {response.status_code}\t{response.text}")

    def handle_failed_batch(self, batch):
        new_batch = [f for f in batch]  # if f["instanceId"] not in self.failed_ids]
        # print(f"2 {len(batch)}")
        """
        for it in batch:
            batch_string = json.dumps(it)
            for id in self.failed_ids:
                if id in batch_string:
                    print(f"id found {id}, removing.")
                elif it not in new_batch:
                    new_batch.append(it)"""
        print(
            f"reposting new batch {len(self.failed_ids)} {len(batch)} {len(new_batch)}",
            flush=True,
        )
        self.post_batch(new_batch, True)

    def do_post(self, batch):
        data = {self.object_name: batch}
        path = self.api_path
        url = self.folio_client.okapi_url + path
        return requests.post(
            url, data=json.dumps(data), headers=self.folio_client.okapi_headers
        )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile", help="path data file")
    parser.add_argument("okapi_url", help=("OKAPI base url"))
    parser.add_argument("tenant_id", help=("id of the FOLIO tenant."))
    parser.add_argument("username", help=("the api user"))
    parser.add_argument("password", help=("the api users password"))
    parser.add_argument("batch_size", help=("batch size"))
    parser.add_argument("api_path", help=("batch size"))
    parser.add_argument("object_name", help=("batch size"))
    parser.add_argument("id_map_path", help=("batch size"))
    args = parser.parse_args()
    return args


def chunks(list, number_of_chunks):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(list), number_of_chunks):
        yield list[i : i + number_of_chunks]


def main():
    """Main Method. Used for bootstrapping. """
    # Parse CLI Arguments
    args = parse_args()

    # Connect to a FOLIO tenant
    folio_client = FolioClient(
        args.okapi_url, args.tenant_id, args.username, args.password
    )
    with open(args.id_map_path, "r") as holdings_id_map_file:
        holdings_id_map = json.load(holdings_id_map_file)
        # Initiate Worker
        worker = Worker(
            folio_client,
            args.datafile,
            args.batch_size,
            args.api_path,
            args.object_name,
            holdings_id_map,
        )

        # Do work
        worker.work()


if __name__ == "__main__":
    """This is the Starting point for the script"""
    main()
