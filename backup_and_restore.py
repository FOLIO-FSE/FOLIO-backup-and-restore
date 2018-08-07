import argparse
import json
import requests


class Backup:
    def __init__(self, endpoint, headers, path):
        self.endpoint = endpoint
        self.headers = headers
        self.path = path
        print('initializing Backup')

    def backup(self, settings):
        for setting in settings:
            print("saving setting {}".format(setting['name']))
            try:
                self.save_one_setting(setting['name'],
                                      setting['path'],
                                      setting['queryString'])
            except Exception as inst:
                print(inst)

    def save_one_setting(self, setting_name, settings_path, query_string):
        query = query_string or ''
        req = requests.get(self.endpoint+settings_path+query,
                           headers=self.headers)
        res = json.loads(req.text)[setting_name]
        setting = {'name': setting_name,
                   'data': res}
        with open(self.path+setting_name+'.json', 'w+') as settings_file:
            settings_file.write(json.dumps(setting))


class Restore:
    def __init__(self, endpoint, headers, path):
        self.endpoint = endpoint
        self.headers = headers
        self.path = path
        print('initializing Restore')

    def restore(self, configuration):
        for setting in configuration:
            try:
                self.restore_one_setting(setting['name'],
                                         setting['path'],
                                         setting['insertMethod'])
            except Exception as inst:
                print(inst)

    def restore_one_setting(self, setting_name, settings_path, method):
        with open(self.path + setting_name + '.json') as settings_file:
            setting = json.load(settings_file)
            for item in setting['data']:
                if(method == "post"):
                    req = requests.put(self.endpoint + settings_path,
                                       data=json.dumps(item),
                                       headers=self.headers)
                    print(req.status_code)

                if(method == "post"):
                    req = requests.post(self.endpoint + settings_path,
                                        data=json.dumps(item),
                                        headers=self.headers)
                    print(req.status_code)


parser = argparse.ArgumentParser()
parser.add_argument("function", help="backup or restore...")
parser.add_argument("from_path", help="path to file holdings the items")


parser.add_argument("okapi_url",
                    help="url of your FOLIO OKAPI endpoint. See settings->software version in FOLIO")
parser.add_argument("tenant_id",
                    help="id of the FOLIO tenant. See settings->software version in FOLIO")
parser.add_argument("okapi_token",
                    help="the x-okapi-token. Easiest optained via F12 in the webbrowser")

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
