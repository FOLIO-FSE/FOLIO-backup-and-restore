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
        csv.register_dialect("tsv", delimiter="\t")
        self.folio_client = folio_client
        self.user_list = {}
        with open(args.file_path) as location_map_f:
            self.user_list = list(csv.DictReader(location_map_f, dialect="tsv"))

    def work(self):
        permissions = set()
        for user in self.user_list:
            permission = user["PERMISSION GROUP"].strip()
            user_id = user["USER ID"].strip()
            permissions.add(permission)
            url = f"{self.folio_client.okapi_url}/perms/users"
            print(f'checking for existing user{url}?query=(userId=="{user_id}")')
            req = requests.get(
                url + f'?query=(userId=="{user_id}")',
                headers=self.folio_client.okapi_headers,
            )
            if req.status_code == 200:
                resp = json.loads(req.text)
                if resp["totalRecords"] == 0:
                    permission_user = json.dumps(
                        {"userId": user_id, "permissions": [permission],}
                    )
                    print(
                        f"user {user_id}) not found. Adding Permissions User record {permission_user} to {url}"
                    )
                    post_resp = requests.post(
                        url,
                        headers=self.folio_client.okapi_headers,
                        data=permission_user,
                    )
                    if post_resp.status_code == 201:
                        print(f"OK! Added user {user_id} with permission {permission}")
                    else:
                        print(
                            f"ERROR {post_resp.status_code} adding user {user_id} with permission {permission} {post_resp.text}"
                        )
                else:
                    print(f"FOUND!\t{permission}\t{req.status_code}")
                    existing_perm_user = resp["permissionUsers"][0]
                    if permission not in existing_perm_user["permissions"]:
                        existing_perm_user["permissions"].append(permission)
                        print(
                            f"user {user_id}) found. Appending Permission to Permission User record {permission_user} to {url}"
                        )
                        put_resp = requests.put(
                            url + f"/{user_id}",
                            headers=self.folio_client.okapi_headers,
                            data=json.dumps(existing_perm_user),
                        )
                        if put_resp.status_code == 201:
                            print(
                                f"Successfully added user {user_id} with permission {permission}"
                            )
                        else:
                            print(
                                f"ERROR {put_resp.status_code} adding user {user_id} with permission {permission}"
                            )
                    else:
                        print("Already has permission")
            else:
                print(req.status_code)


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


def main():
    args = parse_args()
    folio_client = FolioClient(
        args.okapi_url, args.tenant_id, args.username, args.password
    )
    worker = Worker(folio_client, args)
    worker.work()


if __name__ == "__main__":
    main()
