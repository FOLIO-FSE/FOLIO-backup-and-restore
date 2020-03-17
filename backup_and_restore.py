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
            raise Exception("No setting provided. Halting...")

    def purge_one_setting(self, config):
        save_entire_respones = config['saveEntireResponse']
        query = ('queryString' in config and config['queryString']) or ''
        url = self.folio_client.okapi_url + config['path'] + query
        print("Fetching from: {}".format(url))
        page_size = 100
        req = self.make_request(url, 0, page_size)
        j = json.loads(req.text)
        total_recs = int(j['totalRecords'])
        res = list(self.parse_result(j, save_entire_respones, config))
        if total_recs > page_size and not save_entire_respones:
            my_range = list(range(page_size, total_recs, page_size))
            for offset in my_range:
                resp = self.make_request(url, offset, page_size)
                k = json.loads(resp.text)
                ll = self.parse_result(
                    k, save_entire_respones, config)
                res.extend(ll)
        print(f"records to purge {len(res)}", flush=True)
        for i in res:
            try:
                ident = i['id'] if 'id' in i else i['recordId']
                url = self.folio_client.okapi_url + \
                    config['path'] + '/' + ident
                print(url, flush=True)
                headers = self.folio_client.okapi_headers
                req = requests.delete(url, headers=headers)
                print(req.status_code, flush=True)
                if not str(req.status_code).startswith('2'):
                    print(req.text, flush=True)
                    print(json.dumps(req.json), flush=True)
            except Exception as ee:
                print("ERROR=================================", flush=True)
                print(ee, flush=True)

    def parse_result(self, json, save_entire_respones, config):
        if save_entire_respones:
            return json
        elif config['name'] in json:
            return json[config['name']]
        elif 'data' in json:
            return json['data']
        print("no parsing of response", flush=True)

    def make_request(self, path, start, length):
        query = '?limit={}&offset={}'.format(length, start)
        # print(f"PATH: {path + query}")
        req = requests.get(path + query.format(length, start),
                           headers=self.folio_client.okapi_headers)
        if req.status_code != 200:
            print(req.text, flush=True)
            raise ValueError("Request failed {}".format(req.status_code))
        return req


class Backup:
    def __init__(self, folioclient, path, set_name):
        self.folio_client = folio_client
        self.path = path
        self.set_name = set_name
        print('initializing Backup', flush=True)

    def load_schema(self, schema_location):
        req = requests.get(schema_location)
        return json.loads(req.text)

    def make_request(self, path, start, length):
        query = '?limit={}&offset={}'.format(length, start)
        print(path + query)
        req = requests.get(path + query.format(length, start),
                           headers=self.folio_client.okapi_headers)
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
        url = self.folio_client.okapi_url + config['path'] + query
        print("Fetching from: {}".format(url))
        try:
            save_entire_respones = config['saveEntireResponse']
            print(config)
            page_size = 100
            req = self.make_request(url, 0, page_size)
            j = json.loads(req.text)
            total_recs = int(j['totalRecords'])
            res = list(self.parse_result(j, save_entire_respones, config))
            if total_recs > page_size and not save_entire_respones:
                my_range = list(range(page_size, total_recs, page_size))
                for offset in my_range:
                    resp = self.make_request(url, offset, page_size)
                    k = json.loads(resp.text)
                    ll = self.parse_result(k, save_entire_respones, config)
                    res.extend(ll)
            print(f"found {len(res)} records. Saving...")
            if len(res) > 0:
                setting = {'name': config['name'],
                           'data': res}
                filename = config['name'] + ".json"
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
    def __init__(self, folio_client, path, set_name):
        self.folio_client = folio_client
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
        filename = config['name'] + ".json"
        path = pathlib.Path(self.path) / filename
        print("Path: {}".format(path))
        with pathlib.Path.open(path) as refdata_file:
            refdata = json.load(refdata_file)
            print("Restoring {}".format(config['name']))
            for item in refdata['data']:
                try:
                    url = self.folio_client.okapi_url + config['path']
                    headers = self.folio_client.okapi_headers
                    if(config['insertMethod'] == "put"):
                        req = requests.put(url, data=json.dumps(item),
                                           headers=headers)
                        print(req.status_code)
                    if(config['insertMethod'] == "post"):
                        req = requests.post(url, data=json.dumps(item),
                                            headers=headers)
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

if (args.function == 'backup'):
    print("Backup")
    backup = Backup(folio_client, args.from_path, args.set_name)
    backup.backup(configuration)
if (args.function == 'restore'):
    print("Restore")
    restore = Restore(folio_client, args.from_path, args.set_name)
    restore.restore(configuration)
if (args.function == 'purge'):
    print("purge")
    purge = Purge(folio_client, args.from_path, args.set_name)
    purge.purge(configuration)
