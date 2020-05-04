import argparse
import pathlib
import json
import requests
import xml
import xml.etree.ElementTree as ET
import collections
from folioclient.FolioClient import FolioClient


def add_stats(stats, a):
    if a not in stats:
        stats[a] = 1
    else:
        stats[a] += 1


parser = argparse.ArgumentParser()
parser.add_argument("okapi_url",
                    help=("url of your FOLIO OKAPI endpoint."
                          "See settings->software version in FOLIO"))
parser.add_argument("tenant_id",
                    help=("id of the FOLIO tenant. "
                          "See settings->software version in FOLIO"))
parser.add_argument("username", help=("the api user"))
parser.add_argument("password", help=("the api users password"))
args = parser.parse_args()
print(f'{args.tenant_id} {args.username} {args.okapi_url}')
folio_client = FolioClient(args.okapi_url, args.tenant_id, args.username,
                           args.password)

path1 = '/inventory/instances?query=(identifiers=="*\\"value\\": \\"\\"*")&limit=600'
print(path1)
i = 0
stats = {}
failed = list()
response = folio_client.folio_get(path1, 'instances')
print(len(response))
for instance in response:
    i+=1
    empty_types = [f['identifierTypeId'] for f in instance['identifiers'] if not f['value']]
    all_types = [f['identifierTypeId'] for f in instance['identifiers'] if f['value']]
    for e in empty_types:
        if e == '4f3c4c2c-8b04-4b54-9129-f732f1eb3e14':
            if instance['hrid'].startswith('http://libris.kb.se/bib'):
                add_stats(stats, 'hrid is bib-id')
            if '925c7fb9-0b87-4e16-8713-7f4ea71d854b' in all_types:
                add_stats(stats, f"emty short but long xl")


def get_libris_xl_id(bib_id):
    print("")



print(stats)
print(json.dumps(failed, indent=4))
