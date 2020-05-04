import argparse
import pathlib
import json
import requests
import copy
import xml
import xml.etree.ElementTree as ET
import collections
from folioclient.FolioClient import FolioClient


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

path1 = '/users?limit=30&query=(expirationDate="2020-01-31*")&limit=2000'
print(path1)
i = 0
stats = {}
failed = list()
response = folio_client.folio_get(path1, "users")
print(len(response))
for user in response:
    if not user["expirationDate"].startswith("2020-01-31"):
        raise Exception(f"wrong expiration date {user['expirationDate']}")
    user_to_post = copy.deepcopy(user)
    del user_to_post["metadata"]
    user_to_post["active"] = True
    user_to_post["expirationDate"] = "2021-01-31T00:00:00.000+0000"
    put_user(folio_client, user_to_post)
    print(f"PUT /users/{user['id']} {json.dumps(user_to_post)}")
    i += 1
print(i)


print(stats)
print(json.dumps(failed, indent=4))
