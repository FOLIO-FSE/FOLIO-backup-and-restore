import argparse
import pathlib
from urllib.parse import urlparse
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


def delete_request(folio_client, path, object_id, force=False):
    parsed_path = path.rstrip("/").lstrip("/")
    url = f"{folio_client.okapi_url}/{parsed_path}/{object_id}"
    if force:
        print(f"DELETE {url}")
        req = requests.delete(url, headers=folio_client.okapi_headers)
        print(req.status_code)
        print(req.text)
        req.raise_for_status()
    else:
        print(f"Dry run: DELETE {url}")


parser = argparse.ArgumentParser()
parser.add_argument(
    "path_and_query", help=("path and query to stuff to delete."),
)
parser.add_argument(
    "object_name", help=("the object name of the thing to delete"),
)
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
parser.add_argument(
    "-force",
    "-f",
    help=("Using this parameter will make the deletes happen"),
    action="store_true",
)
args = parser.parse_args()

print(f"{args.tenant_id} {args.username} {args.okapi_url} {args.path_and_query}")
folio_client = FolioClient(args.okapi_url, args.tenant_id, args.username, args.password)
pr = urlparse(args.path_and_query)
path1 = pr.path
query = pr.query
print(f"{args.force}")
print(f"path: {path1} query: {query}")
i = 0
stats = {}
failed = set()
objects = folio_client.folio_get_all(path1, args.object_name, f"?{query}")
print(len(objects))
for obj in objects:
    try:
        delete_request(folio_client, path1, obj["id"], args.force)
    except Exception as ee:
        print(ee)
        traceback.print_exc()
        failed.add(obj["id"])
    i += 1
print(i)
print(json.dumps(list(failed), indent=4))
