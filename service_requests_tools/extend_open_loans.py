import argparse
import pathlib
import json
import copy
import requests
import traceback
import xml
import xml.etree.ElementTree as ET
import collections
from folioclient.FolioClient import FolioClient


def add_stats(stats, a):
    if a not in stats:
        stats[a] = 1
    else:
        stats[a] += 1


def put_loan(folio_client, loan):
    url = f"{folio_client.okapi_url}/circulation/loans/{loan['id']}"
    print(url)
    req = requests.put(url, headers=folio_client.okapi_headers, data=json.dumps(loan))
    print(req.status_code)
    req.raise_for_status()


parser = argparse.ArgumentParser()
parser.add_argument(
    "okapi_url",
    help=(
        "url of your FOLIO OKAPI endpoint." "See settings->software version in FOLIO"
    ),
)
parser.add_argument(
    "tenant_id",
    help=("id of the FOLIO tenant. " "See settings->software version in FOLIO"),
)
parser.add_argument("username", help=("the api user"))
parser.add_argument("password", help=("the api users password"))
args = parser.parse_args()
print(f"{args.tenant_id} {args.username} {args.okapi_url}")
folio_client = FolioClient(args.okapi_url, args.tenant_id, args.username, args.password)
patron_emails = set()
path1 = "/circulation/loans"
query = '?query=(status.name="Open" AND dueDate < "2020-05-14*")'
print(f"path: {path1} query: {query}")
i = 0
stats = {}
failed = list()
loans = folio_client.folio_get_all(path1, "loans", query)
print(len(loans))
for loan in loans:
    loan_to_put = copy.deepcopy(loan)
    del loan_to_put["metadata"]
    loan_to_put["dueDate"] = "2020-05-14T21:59:59.000+0000"
    print(loan_to_put["dueDate"])
    try:
        put_loan(folio_client, loan_to_put)
        print(
            f"PUT /circulation/loans/{loan_to_put['id']}\t{json.dumps(loan_to_put)}\t{loan}]"
        )
        # patron = folio_client.folio_get_single_object(f"/users/{loan['userId']}")
        # patron_emails.add(patron["personal"]["email"])
    except Exception as ee:
        print(
            f"ERROR! {i} PUT /circulation/loans/{loan_to_put['id']}\t{json.dumps(loan_to_put)}\t{loan}]"
        )
        print(ee)
        traceback.print_exc()
        raise ee
    i += 1
print(i)

print(patron_emails)
print(stats)
print(json.dumps(failed, indent=4))
