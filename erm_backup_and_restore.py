import argparse
import os.path
import pathlib
import json
import requests
from folioclient.FolioClient import FolioClient


class Backup:
    def __init__(self, folioclient, path):
        self.folioclient = folioclient
        self.path = path
        print('initializing Backup')

    def load_schema(self, schema_location):
        req = requests.get(schema_location)
        return json.loads(req.text)

    def backup(self):
        self.save_erm_refdata()
        self.save_licences_refdata()
        self.save_licences_custprops()
        print(f"Done backing up. files saved to {self.path}")
        self.save_licenses()
        self.save_agreements()

    def save_erm_refdata(self):
        self.get_erm_data('/erm/refdata', 'erm_refdata.json')

    def save_licences_refdata(self):
        self.get_erm_data('/licenses/refdata', 'licenses_refdata.json')

    def save_licences_custprops(self):
        self.get_erm_data('/licenses/custprops', 'licenses_custprops.json')

    def save_licenses(self):
        self.get_erm_data('/licenses/licenses', 'licenses.json')

    def save_agreements(self):
        self.get_erm_data('/erm/sas', 'erm_agreements.json')

    def get_erm_data(self, path, filename):
        perpage = 10
        page = 1
        query = "{}?perPage={}&page={}"
        data_to_save = []
        response = self.folioclient.folio_get_single_object(
            query.format(path, perpage, page))
        with open(os.path.join(self.path, filename), 'w+') as file:
            while len(response) == perpage:
                data_to_save.extend(response)
                page += 1
                print(f"Fetching from {query.format(path, perpage,page)}")
                response = self.folioclient.folio_get_single_object(
                    query.format(path, perpage, page))
            data_to_save.extend(response)
            file.write(json.dumps(data_to_save, indent=4))
            print(
                f"No more objects to fetch. {len(data_to_save)} in total")


class Restore:
    def __init__(self, folioclient, path):
        self.folioclient = folioclient
        self.path = path
        print('initializing Restore')

    def restore(self):
        self.restore_erm_refdata()
        self.restore_licences_custprops()
        self.restore_licences_refdata()
        self.restore_licenses()
        self.restore_agreements()

    def restore_erm_refdata(self):
        self.restore_one("/erm/refdata", 'erm_refdata.json')

    def restore_licences_refdata(self):
        self.restore_one("/licenses/refdata", 'licenses_refdata.json')

    def restore_licences_custprops(self):
        self.restore_one("/licenses/custprops", 'licenses_custprops.json')

    def restore_licenses(self):
        raise Exception("Not implemented")

    def restore_agreements(self):
        raise Exception("Not implemented")

    def restore_one(self, short_path, filename):
        path = self.folioclient.okapi_url + short_path
        f_path = os.path.join(self.path, filename)
        with open(f_path, 'r') as file:
            refdata = json.load(file)
            for refdatavalue in refdata:
                print(f"POST {path}\n\n{json.dumps(refdatavalue, indent=4)}")
                req = requests.post(path,
                                    data=json.dumps(refdatavalue),
                                    headers=self.folioclient.okapi_headers)
                print(req.status_code, flush=True)
                if (str(req.status_code).startswith('4') or
                        str(req.status_code).startswith('5')):
                    print(req.text)
                    print(json.dumps(req.json))


parser = argparse.ArgumentParser()
parser.add_argument("function", help="backup or restore...")
parser.add_argument("from_path", help="path to file holdings the items")


parser.add_argument("okapi_url",
                    help=("url of your FOLIO OKAPI endpoint."
                          "See settings->software version in FOLIO"))
parser.add_argument("tenant_id",
                    help=("id of the FOLIO tenant. "
                          "See settings->software version in FOLIO"))
parser.add_argument("username", help=("the api user"))
parser.add_argument("password", help=("the api users password"))
args = parser.parse_args()

print('Performing {} of FOLIO tenant {} at {} ...'.format(args.function,
                                                          args.tenant_id,
                                                          args.okapi_url))
folio_client = FolioClient(
    args.okapi_url, args.tenant_id, args.username,
    args.password)
if (args.function == 'backup'):
    print("Backup")
    backup = Backup(folio_client, args.from_path)
    backup.backup()
if (args.function == 'restore'):
    print("Restore")
    restore = Restore(folio_client, args.from_path)
    restore.restore()
