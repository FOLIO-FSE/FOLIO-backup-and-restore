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


def add_stats(stats, a):
    if a not in stats:
        stats[a] = 1
    else:
        stats[a] += 1


def parse_args():
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


def check_out_by_barcode(
    folio_client, item_barcode, patron_barcode, loan_date: datetime, service_point_id
):
    try:
        df = "%Y-%m-%dT%H:%M:%S.%f+0000"
        data = {
            "itemBarcode": item_barcode,
            "userBarcode": patron_barcode,
            "loanDate": loan_date.strftime(df),
            "servicePointId": service_point_id,
        }
        path = "/circulation/check-out-by-barcode"
        url = f"{folio_client.okapi_url}{path}"
        print(f"POST {url}\t{json.dumps(data)}", flush=True)
        req = requests.post(
            url, headers=folio_client.okapi_headers, data=json.dumps(data)
        )
        print(req.status_code, flush=True)
        if str(req.status_code) == "422":
            print(
                f"{json.loads(req.text)['errors'][0]['message']}\t{json.dumps(data)}",
                flush=True,
            )
        elif str(req.status_code) == "201":
            return json.loads(req.text)
        else:
            req.raise_for_status()
    except Exception as exception:
        traceback.print_exc()
        print(exception, flush=True)


def extend_open_loan(folio_client, loan):
    try:
        df = "%Y-%m-%dT%H:%M:%S.%f+0000"
        loan_to_put = copy.deepcopy(loan)
        del loan_to_put["metadata"]
        loan_to_put["dueDate"] = fake.date_time_between(
            start_date="-1y", end_date="now"
        ).strftime(df)
        url = f"{folio_client.okapi_url}/circulation/loans/{loan_to_put['id']}"
        print(
            f"PUT Extend loan to {loan_to_put['dueDate']}\t  {url}\t{json.dumps(loan_to_put)}",
            flush=True,
        )
        req = requests.put(
            url, headers=folio_client.okapi_headers, data=json.dumps(loan_to_put)
        )
        print(req.status_code)
        if str(req.status_code) == "422":
            print(
                f"{json.loads(req.text)['errors'][0]['message']}\t{json.dumps(loan_to_put)}",
                flush=True,
            )
        else:
            req.raise_for_status()
    except Exception as exception:
        traceback.print_exc()
        print(exception, flush=True)


def make_request(
    folio_client,
    request_type,
    patron,
    item,
    service_point_id,
    request_date=datetime.now(),
):
    try:
        df = "%Y-%m-%dT%H:%M:%S.%f+0000"
        data = {
            "requestType": request_type,
            "fulfilmentPreference": "Hold Shelf",
            "requester": {"barcode": patron["barcode"]},
            "requesterId": patron["id"],
            "item": {"barcode": item["barcode"]},
            "itemId": item["id"],
            "pickupServicePointId": service_point_id,
            "requestDate": request_date.strftime(df),
        }
        path = "/circulation/requests"
        url = f"{folio_client.okapi_url}{path}"
        print(f"POST {url}\t{json.dumps(data)}", flush=True)
        req = requests.post(
            url, headers=folio_client.okapi_headers, data=json.dumps(data)
        )
        print(req.status_code, flush=True)
        if str(req.status_code) == "422":
            print(
                f"{json.loads(req.text)['errors'][0]['message']}\t{json.dumps(data)}",
                flush=True,
            )
        else:
            print(req.status_code, flush=True)
            # print(req.text)
            req.raise_for_status()
    except Exception as exception:
        print(exception, flush=True)
        traceback.print_exc()


def get_random_objects(folio_client, path, count=1, query=""):
    resp = folio_client.folio_get(path)
    total = int(resp["totalRecords"])
    name = next(f for f in [*resp] if f != "totalRecords")
    rand = random.randint(0, total)
    query = f"?limit={count}&offset={rand}"
    print(f"{total} found, {rand} to pick")
    return iter(folio_client.folio_get(path, name, query))


def get_all_ids(folio_client, path, query=""):
    resp = folio_client.folio_get(path)
    name = next(f for f in [*resp] if f != "totalRecords")
    gs = folio_client.folio_get_all(path, name, query)
    ids = [f["id"] for f in gs]
    print(len(ids), flush=True)
    return ids


fake = Faker()
args = parse_args()
loan_policies = {}
print(f"{args.tenant_id} {args.username} {args.okapi_url}", flush=True)
folio_client = FolioClient(args.okapi_url, args.tenant_id, args.username, args.password)
patron_groups = get_all_ids(folio_client, "/groups")
item_loan_types = get_all_ids(folio_client, "/loan-types")
item_material_types = get_all_ids(folio_client, "/material-types")
service_points = get_all_ids(
    folio_client, "/service-points", "?query=(pickupLocation==true)"
)
locations = get_all_ids(folio_client, "/locations")
item_seeds = list(itertools.product(item_material_types, item_loan_types, locations))
random.shuffle(item_seeds)
print(len(item_seeds))
items = set()
for seed in item_seeds:
    material_type_id = seed[0]
    loan_type_id = seed[1]
    location_id = seed[2]
    i_query = f'?query=(materialTypeId="{seed[0]}" and permanentLoanTypeId="{seed[1]}" and effectiveLocationId="{seed[2]}" and status.name=="Available")'
    for patron_group_id in patron_groups:
        items = get_random_objects(
            folio_client, "/item-storage/items", 10, query=i_query
        )
        p_query = f'query=(patronGroup=="{patron_group_id}" and active==true)'
        patrons = get_random_objects(folio_client, "/users", 10, p_query)
        item_patrons = zip(items, patrons)
        for item_patron in item_patrons:
            if "barcode" in item_patron[1] and "barcode" in item_patron[0]:
                service_point_id = random.choice(service_points)
                if random.randint(0, 5) > 0:
                    print("create loan", flush=True)
                    # loan_date = fake.date_time_between(start_date="-1y", end_date="now")
                    loan = check_out_by_barcode(
                        folio_client,
                        item_patron[0]["barcode"],
                        item_patron[1]["barcode"],
                        datetime.now(),
                        service_point_id,
                    )
                    if loan:
                        extend_open_loan(folio_client, loan)
                else:
                    print("create page request", flush=True)
                    make_request(
                        folio_client,
                        "Page",
                        item_patron[1],
                        item_patron[0],
                        service_point_id,
                    )
                for b in random.sample(range(30), random.randint(1, 4)):
                    new_patron = next(
                        get_random_objects(folio_client, "/users", 1, p_query)
                    )
                    make_request(
                        folio_client,
                        random.choice(["Hold", "Recall"]),
                        new_patron,
                        item_patron[0],
                        service_point_id,
                    )
