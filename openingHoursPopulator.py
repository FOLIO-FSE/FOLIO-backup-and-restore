import pathlib
import requests
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("operation", help="result file path")
parser.add_argument("path", help="result file path")
parser.add_argument("okapi_url", help="url of your FOLIO OKAPI endpoint.")
parser.add_argument("tenant_id", help="id of the FOLIO tenant")
parser.add_argument("okapi_token", help="the x-okapi-token")

args = parser.parse_args()
okapiHeaders = {'x-okapi-token': args.okapi_token,
                'x-okapi-tenant': args.tenant_id,
                'content-type': 'application/json'}
if str(args.operation) == 'backup':
    periods_query = "?withOpeningDays=true&showPast=true&showExceptional"
    periods_path = "/calendar/periods/{}/period{}"

    sp_request = requests.get(args.okapi_url + '/service-points',
                              headers=okapiHeaders)
    sp_json = json.loads(sp_request.text)
    service_points_ids = [sp['id'] for sp
                          in sp_json['servicepoints']]
    periods_to_save = {}
    for sp_id in service_points_ids:
        query = periods_path.format(sp_id, periods_query)
        period_req = requests.get(args.okapi_url + query,
                                  headers=okapiHeaders)
        periods_resp = json.loads(period_req.text)
        periods_to_save[sp_id] = periods_resp
    with open(args.path, 'w+') as settings_file:
        settings_file.write(json.dumps(periods_to_save))

if args.operation == 'restore':
    with open(args.path) as settings_file:
        js = json.load(settings_file)
        for sp_id, periods in js.items():
            if any(periods['openingPeriods']):
                period = periods['openingPeriods'][0]
                periods_path = "/calendar/periods/{}/period".format(sp_id)
                # print("{}, {}".format(sp_id, period['openingPeriods'][0]))
                req = requests.post(args.okapi_url + periods_path,
                                    data=json.dumps(period),
                                    headers=okapiHeaders)
                print(req.status_code)
                print(req.text)
                if str(req.status_code).startswith('4'):
                    print(req.text)
