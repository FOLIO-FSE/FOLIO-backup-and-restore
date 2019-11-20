import argparse
import pathlib
import json
import requests


class Backup:
    def __init__(self, endpoint, headers, path, set_name):
        self.endpoint = endpoint
        self.headers = headers
        self.path = path
        self.set_name = set_name
        print('initializing Backup')

    def load_schema(self, schema_location):
        req = requests.get(schema_location)
        return json.loads(req.text)

    def make_request(self, path, start, length):
        query = '?limit={}&offset={}'.format(length, start)
        print(path+query)
        req = requests.get(path+query.format(length, start),
                           headers=self.headers)
        if req.status_code != 200:
            print(req.text)
            raise ValueError("Request failed {}".format(req.status_code))
        return req

    def parse_result(self, json, save_entire_respones, config):
        if save_entire_respones:
            return json
        elif config['name'] in json:
            return json[config['name']]
        elif 'data' in json:
            return json['data']
        print("no parsing of response")

    def backup(self, settings):
        if self.set_name:
            print("saving setting {}".format(self.set_name))
            setting = next(s for s in settings if s['name'] == self.set_name)
            self.save_one_setting(setting)
        else:
            for setting in settings:
                print("saving setting {}".format(setting['name']))
                self.save_one_setting(setting)

    def save_one_setting(self, config):
        query = ('queryString' in config and config['queryString']) or ''
        url = self.endpoint+config['path']+query
        print("Fetching from: {}".format(url))
        try:
            save_entire_respones = config['saveEntireResponse']
            print(config)
            page_size = 100
            req = self.make_request(url, 0, page_size)
            j = json.loads(req.text)
            res = self.parse_result(j, save_entire_respones, config)
            # total_recs = int(j['totalRecords'])
            # if total_recs > page_size and not save_entire_respones:
            #     my_range = range(page_size, total_recs, page_size)
            #     print(my_range)
            #     for offset in my_range:
            #         resp = self.make_request(url, offset, page_size)
            #         j = json.loads(req.text)
            #         res.append(j[config['name']])
            print(len(res))
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
    def __init__(self, endpoint, headers, path, set_name):
        self.endpoint = endpoint
        self.headers = headers
        self.path = path
        self.set_name = set_name
        print('initializing Restore')

    def restore(self, settings):
        if self.set_name:
            print("restoring setting {}".format(self.set_name))
            setting = next(s for s in settings if s['name'] == self.set_name)
            self.restore_one_setting(setting)
        else:
            for setting in settings:
                self.restore_one_setting(setting)

    def restore_one_setting(self, config):
        filename = config['name']+".json"
        path = pathlib.Path(self.path) / filename
        print("Path: {}".format(path))
        with pathlib.Path.open(path) as refdata_file:
            refdata = json.load(refdata_file)
            print("Restoring {}".format(config['name']))
            for item in refdata['data']:
                try:
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


def get_token(url, tenant_id, username, password):
    '''Logs into FOLIO in order to get the okapi token'''
    try:
        headers = {
            'x-okapi-tenant': tenant_id,
            'content-type': 'application/json'}
        payload = {"username": username,
                   "password": password}
        url = url + "/authn/login"
        req = requests.post(url, data=json.dumps(payload), headers=headers)
        if req.status_code != 201:
            print(req.status_code)
            print(req.text)
            raise ValueError("Request failed {}".format(req.status_code))
        return req.headers.get('x-okapi-token')
        # req.headers.get('refreshtoken')]
    except Exception as exception:
        print("Failed login request. No login token acquired.")
        raise exception


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
parser.add_argument("settings_file",
                    help=("path to settings file"))
parser.add_argument('-s', '--set_name', help='foo help')
args = parser.parse_args()
okapi_token = get_token(args.okapi_url, args.tenant_id,
                        args.username, args.password)
okapi_headers = {'x-okapi-token': okapi_token,
                 'x-okapi-tenant': args.tenant_id,
                 'content-type': 'application/json'}
print('Performing {} of FOLIO tenant {} at {} ...'.format(args.function,
                                                          args.tenant_id,
                                                          args.okapi_url))
with open(args.settings_file) as settings_file:
    configuration = json.load(settings_file)

if (args.function == 'backup'):
    print("Backup")
    backup = Backup(args.okapi_url, okapi_headers, args.from_path,
                    args.set_name)
    backup.backup(configuration)
if (args.function == 'restore'):
    print("Restore")
    restore = Restore(args.okapi_url, okapi_headers, args.from_path,
                      args.set_name)
    restore.restore(configuration)
