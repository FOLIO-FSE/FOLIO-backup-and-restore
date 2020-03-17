import argparse
import pathlib
import json
import requests
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

folio_client = FolioClient(args.okapi_url, args.tenant_id, args.username,
                           args.password)

path1 = "/scheduled-notice-storage/scheduled-notices"
query_temp = '?limit={}&offset={}'

limit = 100
offset = 0
i = 0
sameids = 0
stats = {}
create_dates = {}
update_dates = {}
statuses = {}

query = query_temp.format(limit, offset)
response = folio_client.folio_get(path1, 'scheduledNotices', query)
while len(response) == limit:
    i += len(response)
    for notice in response:
        if 'recipientUserId' not in notice:
            print(f'Notice lacks recipientUserId:{notice["id"]}')
        elif 'loanId' not in notice:
            print(f'Notice lacks loanId:{notice["id"]}')
        elif notice['recipientUserId'] and notice['loanId'] and notice['loanId'] == notice['recipientUserId']:
            print(
                f'Notice has same loanId as recipientId:{notice["id"]} checking loan...')
            sameids += 1
            path = f"/loan-storage/loans/{notice['loanId']}"
            loan = folio_client.folio_get_single_object(path)
            if (loan['status']['name'] == 'Open'):
                add_stats(stats, loan['loanDate'][0:10])
                add_stats(create_dates,
                          notice['metadata']['createdDate'][0:10])
                add_stats(update_dates,
                          notice['metadata']['updatedDate'][0:10])
                actual_patron_id = loan['userId']
                print(notice)
                notice['recipientUserId'] = actual_patron_id
                print(json.dumps(notice))
                url = f"{folio_client.okapi_url}{path1}/{notice['id']}"
                print(url)
                # req = requests.put(url, data=json.dumps(notice),
                #                   headers=folio_client.okapi_headers)
                # print(req.status_code)
                # print(req.text)
            else:
                add_stats(statuses, loan['status']['name'])

    offset += 1
    query = query_temp.format(limit, offset * limit)
    print(f"{i} Fetching more... sameIds:{sameids}")
    response = folio_client.folio_get(path1, 'scheduledNotices', query)

print(f"No more objects to fetch. {i} in total")
od = collections.OrderedDict(sorted(stats.items()))
print(od)
od = collections.OrderedDict(sorted(create_dates.items()))
print(od)
od = collections.OrderedDict(sorted(update_dates.items()))
print(od)
print(statuses)
