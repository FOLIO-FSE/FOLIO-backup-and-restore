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

path1 = '/instance-storage/instances?query=(hrid=="http://libris.kb.se/bib/*")&limit=300'
i = 0
stats = {}
failed = list()
response = folio_client.folio_get(path1, 'instances')
for instance in response:
    bib_id = next((id['value'] for id in instance["identifiers"]
                    if id['identifierTypeId'] == "925c7fb9-0b87-4e16-8713-7f4ea71d854b"),"")
    if instance['hrid'].startswith('http://libris.kb.se/bib/') and bib_id.startswith("http://libris.kb.se/bib/"):
        add_stats(stats, 'hasBibIdasHrid')
        oai_request = f"https://libris.kb.se/api/oaipmh/?verb=GetRecord&identifier={bib_id}&metadataPrefix=jsonld"
        #print(oai_request)
        resp = requests.get(oai_request)
        root = ET.fromstring(resp.text)
        
        try:
            jsonld = json.loads(root.find("{http://www.openarchives.org/OAI/2.0/}GetRecord").find("{http://www.openarchives.org/OAI/2.0/}record").find("{http://www.openarchives.org/OAI/2.0/}metadata").text)
            xl_id = jsonld['@graph'][0]['@id']
            print(f"Replace hrid\t{bib_id}\twith\t{xl_id}\tfor instance with id\t{instance['id']}")
        except Exception as ee:
            failed.append(f"{oai_request} falerade {instance['id']}")
            error = root.find("{http://www.openarchives.org/OAI/2.0/}error").attrib['code']
            add_stats(stats, error)
    else:
        add_stats(stats, 'hasNoBibId')
    raise Exception("add identifiers to the records")

def get_libris_xl_id(bib_id):
    print("")



print(stats)
print(json.dumps(failed, indent=4))
