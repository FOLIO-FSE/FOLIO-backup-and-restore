import argparse
import pathlib
import json
import requests


class Backup:
    def __init__(self, endpoint, headers, path):
        self.endpoint = endpoint
        self.headers = headers
        self.path = path
        print('initializing Backup')

    def load_schema(self, schema_location):
        req = requests.get(schema_location)
        return json.loads(req.text)

    def backup(self, settings):
        for setting in settings:
            print("saving setting {}".format(setting['name']))
            self.save_one_setting(setting)

    def save_one_setting(self, config):
        query = ('queryString' in config and config['queryString']) or ''
        url = self.endpoint+config['path']+query+'?limit=100'
        print("Fetching from: {}".format(url))
        try:
            req = requests.get(url,
                            headers=self.headers)
            j = json.loads(req.text)
            res = j if config['saveEntireResponse'] else j[config['name']]
            if len(res) > 0:
                setting = {'name': config['name'],
                        'data': res}
                filename = config['name']+".json"
                path = pathlib.Path.cwd() / self.path / filename
                print("Saving to: {}".format(path))
                with pathlib.Path.open(path, 'w+') as settings_file:
                    settings_file.write(json.dumps(setting))
            else:
                print("No data found")
        except Exception as ee:
            print("ERROR=========================={}".format(config['name']))
            print(ee)


class Restore:
    def __init__(self, endpoint, headers, path):
        self.endpoint = endpoint
        self.headers = headers
        self.path = path
        print('initializing Restore')

    def restore(self, configuration):
        for config in configuration:
            self.restore_one_setting(config)

    def restore_one_setting(self, config):
        filename = config['name']+".json"
        path = pathlib.Path(self.path) / filename
        print("Path: {}".format(path))
        try:
            with pathlib.Path.open(path) as refdata_file:
                refdata = json.load(refdata_file)
                print("Restoring {}".format(config['name']))
                for item in refdata['data']:
                    if(config['insertMethod'] == "put"):
                        req = requests.put(self.endpoint + config['path'],
                                           data=json.dumps(item),
                                           headers=self.headers)
                        print(req.status_code)
                    if(config['insertMethod'] == "post"):
                        req = requests.post(self.endpoint + config['path'],
                                            data=json.dumps(item),
                                            headers=self.headers)
                        print(req.status_code)
                        if str(req.status_code).startswith('4'):
                            print(req.text)
                            print(json.dumps(req.json))
        except Exception as ee:
            print("ERROR=================================")
            print(ee)


parser = argparse.ArgumentParser()
parser.add_argument("function", help="backup or restore...")
parser.add_argument("from_path", help="path to file holdings the items")


parser.add_argument("okapi_url",
                    help=("url of your FOLIO OKAPI endpoint."
                          "See settings->software version in FOLIO"))
parser.add_argument("tenant_id",
                    help=("id of the FOLIO tenant. "
                          "See settings->software version in FOLIO"))
parser.add_argument("okapi_token",
                    help=("the x-okapi-token. "
                          "Easiest optained via F12 in the webbrowser"))
parser.add_argument("settings_file",
                    help=("path to settings file"))

args = parser.parse_args()
okapi_headers = {'x-okapi-token': args.okapi_token,
                 'x-okapi-tenant': args.tenant_id,
                 'x-okpapi-user-id': "a058f28f-80ac-4994-add6-e4d02fc238fe",
                 'content-type': 'application/json'}
print('Performing {} of FOLIO tenant {} at {} ...'.format(args.function,
                                                          args.tenant_id,
                                                          args.okapi_url))
with open(args.settings_file) as settings_file:
    configuration = json.load(settings_file)

if (args.function == 'backup'):
    backup = Backup(args.okapi_url, okapi_headers, args.from_path)
    backup.backup(configuration)
if (args.function == 'restore'):
    restore = Restore(args.okapi_url, okapi_headers, args.from_path)
    restore.restore(configuration)
