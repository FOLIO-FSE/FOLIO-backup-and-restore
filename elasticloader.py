import argparse
import pathlib
import json
import requests
from folioclient.FolioClient import FolioClient

parser = argparse.ArgumentParser()
parser.add_argument("indexname", help="name of elastic index")
parser.add_argument("from_path", help="path to file holdings the items")
args = parser.parse_args()

payload = []
index = 0
with open(args.from_path) as datafile:

    for line in datafile:
        index += 1
        payload.append(json.dumps(
            {"index": {"_index": args.indexname, "_id": index}}))
        payload.append('\n')
        payload.append(line)
        if index % 500 == 0:
            print(f"posting {index}")
            response = requests.post('http://127.0.0.1:9200/_bulk',
                                     data=''.join(payload) + '\n',
                                     headers={"Content-Type": 'application/x-ndjson'})
            print(response.status_code, flush=True)
            if (str(response.status_code).startswith('4') or
                    str(response.status_code).startswith('5')):
                print(response.text)
                print(json.dumps(response.json))
            payload = []
