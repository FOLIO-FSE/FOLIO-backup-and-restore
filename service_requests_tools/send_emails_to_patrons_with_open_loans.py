import argparse
import collections
import copy
import json
import pathlib
import traceback
import xml
import xml.etree.ElementTree as ET
import requests

from folioclient.FolioClient import FolioClient


def add_stats(stats, a):
    if a not in stats:
        stats[a] = 1
    else:
        stats[a] += 1


def send_email(email_address):
    """using SendGrid's Python Library
    https://github.com/sendgrid/sendgrid-python"""
    import os
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    message = Mail(
        from_email="support.lib@chalmers.se",
        to_emails=email_address,
        subject="Are you leaving Chalmers? Return your library books!",
        html_content='<p>Hej!</p><p>Slutar du på Chalmers? Kom ihåg att lämna tillbaka dina biblioteksböcker innan du lämnar oss. Bokinkastet är alltid öppet och du hittar det till vänster om huvudentrén på Huvudbiblioteket. Du kan även skicka böcker till oss med post, se adress nedan.</p><p>Chalmers bibliotek är stängt på grund av covid-19. Alla lån förlängs till biblioteken öppnar igen.</p><p>Med vänlig hälsning<br/>Chalmers bibliotek<br/>Chalmers tekniska högskolas bibliotek, 412 96 Göteborg </p><p><a href="http://www.lib.chalmers.se">http://www.lib.chalmers.se</a></p><hr/><p>Hi!</p><p>Are you leaving Chalmers? Don´t forget to return your library books before you leave us. The book drop is always open and you´ll find it at the left side of the main entrance at the Main Library. You can also send the books by mail.<p/><p>Chalmers libraries are closed due to covid-19. All loans are prolonged until the library opens again.</p><p>Regards<br/>Chalmers Library<br/>Chalmers tekniska högskolas bibliotek, SE-412 96 Göteborg </p><p><a href="http://www.lib.chalmers.se/en/">http://www.lib.chalmers.se/en/</a></p>',
    )
    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(f"ERROR SENDING EMAIL: {e} \t {email_address}")
        traceback.print_exc()
        raise e


def get_all_open_loans(folio_client):
    """Get all open loans """
    path1 = "/loan-storage/loans"
    query = ""  # '?query=(status.name="Open")'
    print(f"path: {path1} query: {query}")
    loans = folio_client.folio_get_all(path1, "loans", query)
    print(f"fetched {len(loans)} loans")
    return loans


def get_user_emails(folio_client, user_ids, patron_groups=[]):
    i = 0
    print("")
    for user_id in user_ids:
        i += 1
        filtered_out = 0
        try:
            patron = folio_client.folio_get_single_object(f"/users/{user_id}")
            if patron_groups and patron["patronGroup"] in patron_groups:
                yield patron["personal"]["email"]
            elif patron_groups and patron["patronGroup"] not in patron_groups:
                filtered_out += 1
            elif not patron_groups:
                yield patron["personal"]["email"]
        except Exception as ee:
            print(ee)
            traceback.print_exc()
            raise ee
        if i % 10 == 0:
            print(i, end="\r")
    print(f"filtered out: {filtered_out}")


parser = argparse.ArgumentParser()
parser.add_argument(
    "okapi_url",
    help=(
        "url of your FOLIO OKAPI endpoint." "See settings->software version in FOLIO"
    ),
)
parser.add_argument(
    "tenant_id",
    help=("id of the FOLIO tenant. " "See settings->software version in FOLIO"),
)
parser.add_argument("username", help=("the api user"))
parser.add_argument("password", help=("the api users password"))
args = parser.parse_args()
print(f"{args.tenant_id} {args.username} {args.okapi_url}")
folio_client = FolioClient(args.okapi_url, args.tenant_id, args.username, args.password)

patron_emails = set()
i = 0
loans = get_all_open_loans(folio_client)
print(f"Number of loans: {len(loans)}")
open_loans = [l for l in loans if l["status"]["name"] == "Open"]
print(f"Number of open loans: {len(open_loans)}")
user_ids = list(set([l["userId"] for l in open_loans]))  # [182:]
print(f"Number of users: {len(user_ids)}")
patron_emails = list(
    set(
        get_user_emails(
            folio_client,
            user_ids,
            [
                "c568f50b-a7f3-44ac-9f19-335da89ec6bc",
                "a7528187-78fe-4e33-a89c-c82bd407fcf3",
                "f336c902-ff8b-438f-b4c8-efbe435a7304",
            ],
        )
    )
)
print(f"Number of emails: {len(patron_emails)}")
failed_addresses = []
successfull_addresses = []
for email in patron_emails:
    try:
        send_email(email)
        successfull_addresses.append(email)
    except Exception as ee:
        print("Email failed to send")
        failed_addresses.append(email)
    print(f"{len(successfull_addresses)} success, {len(failed_addresses)} failed")

print(f"Successfull emails sent to these\t{json.dumps(successfull_addresses)}")
print(f"Failed emails NOT sent to these\t{json.dumps(failed_addresses)}")

# print(patron_emails)
