import argparse
import pathlib
import json
import requests
from folioclient.FolioClient import FolioClient


class Purge:
    def __init__(self, folio_client, path, set_name):
        self.folio_client = folio_client
        self.path = path
        self.set_name = set_name
        print('initializing Purge')

    def purge(self, settings):
        if self.set_name:
            print("purge setting {}".format(self.set_name))
            setting = next(s for s in settings if s['name'] == self.set_name)
            self.purge_one_setting(setting)
        else:
            for setting in settings:
                self.purge_one_setting(setting)

    def purge_one_setting(self, config):
        filename = config['name'] + ".json"
        path = pathlib.Path(self.path) / filename
        print("Path: {}".format(path))
        with pathlib.Path.open(path) as refdata_file:
            refdata = json.load(refdata_file)
            print("Restoring {}".format(config['name']))
            for item in refdata['data']:
                try:
                    url = self.folio_client.okapi_url + config['path']+ '/' + item["id"]
                    headers = self.folio_client.okapi_headers
                    req = requests.delete(url, headers=headers)
                    print(req.status_code)
                    if str(req.status_code).startswith('4'):
                        print(req.text)
                        print(json.dumps(req.json))
                except Exception as ee:
                    print("ERROR=================================")
                    print(ee)



        print('Fine Purge')

parser = argparse.ArgumentParser()
parser.add_argument("function", help="purge ...")
parser.add_argument("from_path", help="path to file holdings the items")
parser.add_argument("okapi_url",
                    help=("url of your FOLIO OKAPI endpoint."
                          "See settings->software version in FOLIO"))
parser.add_argument("tenant_id",
                    help=("id of the FOLIO tenant. "
                          "See settings->software version in FOLIO"))
parser.add_argument("username", help=("the api user"))
parser.add_argument("password", help=("the api users password"))
parser.add_argument("settings_file",
                    help=("path to settings file"))
parser.add_argument('-s', '--set_name', help='foo help')
args = parser.parse_args()


print('Performing {} of FOLIO tenant {} at {} ...'.format(args.function,
                                                          args.tenant_id,
                                                          args.okapi_url))
folio_client = FolioClient(
    args.okapi_url, args.tenant_id, args.username,
    args.password)

with open(args.settings_file) as settings_file:
    configuration = json.load(settings_file)

if (args.function == 'purge'):
    print("Purge")
    purge = Purge(folio_client, args.from_path, args.set_name)
    purge.purge(configuration)

