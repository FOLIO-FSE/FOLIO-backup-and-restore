import argparse
import pathlib
import json
import requests
import collections
from datetime import datetime, timedelta
from folioclient.FolioClient import FolioClient


def add_stats(stats, a):
    if a not in stats:
        stats[a] = 1
    else:
        stats[a] += 1


def get_metadata_construct(user_id):
    df = '%Y-%m-%dT%H:%M:%S.%f+0000'
    return {
        "createdDate": datetime.now().strftime(df),
        "createdByUserId": user_id,
        "updatedDate": datetime.now().strftime(df),
        "updatedByUserId": user_id
    }


def get_notice(loan_id, recipient_id, user_id):
    df = '%Y-%m-%dT%H:%M:%S.%f+0000'
    next_run_time = datetime.now() + timedelta(hours=2)
    return {
        "loanId": loan_id,
        "recipientUserId": recipient_id,
        "nextRunTime": next_run_time.strftime(df),
        "triggeringEvent": "Due date",
        "noticeConfig": {
            "timing": "After",
            "templateId": "34dab6c8-f459-49d1-9cf8-c45c013b1349",
            "format": "Email",
            "sendInRealTime": False
        },
        "metadata": get_metadata_construct(user_id)
    }


parser = argparse.ArgumentParser()
parser.add_argument("okapi_url",
                    help=("url of your FOLIO OKAPI endpoint."
                          "See settings->software version in FOLIO"))
parser.add_argument("tenant_id",
                    help=("id of the FOLIO tenant. "
                          "See settings->software version in FOLIO"))
parser.add_argument("username", help=("the api user"))
parser.add_argument("password", help=("the api users password"))
parser.add_argument("user_id", help=("the api users id"))
args = parser.parse_args()
folio_client = FolioClient(args.okapi_url, args.tenant_id, args.username,
                           args.password)

'''Make a test first with Danielle Steele
Bokbinderiet

Post a scheduled notices of template 34dab6c8-f459-49d1-9cf8-c45c013b1349'''

# Get all OVERDUE (dueDate<today) loans that are OPEN
path = '/circulation/loans'
df = '%Y-%m-%d'
overdue_dt = (datetime.now() + timedelta(days=-1)).strftime(df)
query_temp = '?limit={}&offset={}&query=(dueDate<"{}*" AND status.name="Open")'
limit = 100
test_patrons = ['c179adc5-9506-45cc-8f6a-8a0477fc9fb7',
                '156759ba-c4fa-4d89-9cf1-e2b2b8eba5da']
offset = 0
i = 0
stats = {}
create_dates = {}
update_dates = {}
statuses = {}
notices_to_send = list()
query = query_temp.format(limit, offset, overdue_dt)
print(query, flush=True)
response = folio_client.folio_get(path, 'loans', query)
while len(response) == limit:
    i += len(response)
    for loan in response:
        # if loan['userId'] in test_patrons:
        # print(f"FOUND TEST PATRON! {loan['status']}")
        n = get_notice(loan['id'], loan['userId'], args.user_id)
        notices_to_send.append(n)
        url = f"{folio_client.okapi_url}/scheduled-notice-storage/scheduled-notices"
        post_resp = requests.post(url, data=json.dumps(n),
                                  headers=folio_client.okapi_headers)
        if post_resp.status_code == 201:
            print("Ok! 201", flush=True)
        if post_resp.status_code != 201:
            print(post_resp.status_code)
            print(post_resp.text, flush=True)
        add_stats(stats, loan['loanDate'][0:10])
    offset += 1
    query = query_temp.format(limit, offset * limit, overdue_dt)
    print(f"{i} Fetching more...{query}", flush=True)
    response = folio_client.folio_get(path, 'loans', query)

# print(json.dumps(notices_to_send))
print(len(notices_to_send), flush=True)
'''print(f"No more objects to fetch. {i} in total")
od = collections.OrderedDict(sorted(stats.items()))
print(od)
od = collections.OrderedDict(sorted(create_dates.items()))
print(od)
od = collections.OrderedDict(sorted(update_dates.items()))
print(od)
print(statuses)'''
