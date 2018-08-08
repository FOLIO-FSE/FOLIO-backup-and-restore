import argparse
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
        req = requests.get(self.endpoint+config['path']+query,
                           headers=self.headers)
        j = json.loads(req.text)
        res = j if config['saveEntireResponse'] else j[config['name']]
        setting = {'name': config['name'],
                   'data': res}
        with open(self.path+config['name']+'.json', 'w+') as settings_file:
            settings_file.write(json.dumps(setting))


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
        with open(self.path + config['name'] + '.json') as settings_file:
            setting = json.load(settings_file)
            print("Restoring {}".format(config['name']))
            for item in setting['data']:
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
                    print(req.text)
                    if(req.status_code == 422):
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
parser.add_argument("okapi_token",
                    help=("the x-okapi-token. "
                          "Easiest optained via F12 in the webbrowser"))

args = parser.parse_args()
okapi_headers = {'x-okapi-token': args.okapi_token,
                 'x-okapi-tenant': args.tenant_id,
                 'content-type': 'application/json'}
print('Performing {} of FOLIO tenant {} at {} ...'.format(args.function,
                                                          args.tenant_id,
                                                          args.okapi_url))
with open('settings.json') as settings_file:
    configuration = json.load(settings_file)

if (args.function == 'backup'):
    backup = Backup(args.okapi_url, okapi_headers, args.from_path)
    backup.backup(configuration)
if (args.function == 'restore'):
    restore = Restore(args.okapi_url, okapi_headers, args.from_path)
    restore.restore(configuration)
