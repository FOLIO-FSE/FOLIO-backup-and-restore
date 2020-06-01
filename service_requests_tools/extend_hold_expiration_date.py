import argparse
import pathlib
import json
import copy
import requests
import traceback
import xml
import xml.etree.ElementTree as ET
import collections
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
        subject="Ändrade återlämningsdatum. Chalmers bibliotek har stängt till vidare med anledning av Covid-19 / Changed due dates. Chalmers libraries are closed due to Covid-19",
        html_content="<p>&nbsp;</p><p><strong>Alla Chalmers bibliotek har st&auml;ngt tills vidare med anledning av Covid-19, fr&aring;n 18 mars och fram&aring;t.</strong></p><p>Du som har reserverade b&ouml;cker kan f&ouml;r n&auml;rvarande inte h&auml;mta dem p&aring; biblioteket. Reservationerna st&aring;r kvar f&ouml;r din r&auml;kning s&aring; att du kan h&auml;mta dem n&auml;r biblioteket har &ouml;ppnat igen. Utl&aring;ning och best&auml;llning av b&ouml;cker &auml;r inte m&ouml;jlig s&aring; l&auml;nge biblioteket har st&auml;ngt.</p><p>Mer information finns att l&auml;sa p&aring; bibliotekets webbplats http://lib.chalmers.se. Vi hj&auml;lper dig g&auml;rna med olika fr&aring;gor via v&aring;r email-support eller via telefon.</p><p>Chalmers bibliotek<br />Visiting address: H&ouml;rsalsv&auml;gen 2<br />Email: support.lib@chalmers.se<br />Phone: 031-7723737<br /><br />&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;English version</p><p><strong>From March 18 until further notice all Chalmers libraries will be completely closed to visitors.</strong>&nbsp;<br /><br />You have reserved books at the library, but it is currently not possible to pick them up. The reservations remain on your behalf so you can borrow them when the library has re-opened. It&rsquo;s not possible to request or borrow books during this closed period.</p><p>More information at the library web site http://lib.chalmers.se/en. We`ll be happy to answer any questions you might have. Contact information below.&nbsp;</p><p>Chalmers library<br />Visiting address: H&ouml;rsalsv&auml;gen 2<br />Email: support.lib@chalmers.se<br />Phone: 031-7723737</p><p>&nbsp;</p>",
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


def put_request(folio_client, request):
    url = f"{folio_client.okapi_url}/circulation/requests/{request['id']}"
    print(url)
    req = requests.put(
        url, headers=folio_client.okapi_headers, data=json.dumps(request)
    )
    print(req.status_code)
    req.raise_for_status()


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
patron_emails_sucess = set()
path1 = "/circulation/requests"
query = '?query=(status="Awaiting pickup" and holdShelfExpirationDate < "2020-08-14*")'
print(f"path: {path1} query: {query}")
i = 0
stats = {}
failed = set()
requests_l = folio_client.folio_get_all(path1, "requests", query)
print(f"found {len(requests_l)} requests to extend")
for request in requests_l:
    request_to_put = copy.deepcopy(request)
    del request_to_put["metadata"]
    request_to_put["holdShelfExpirationDate"] = "2020-08-14T22:59:59.000+0000"
    print(request_to_put["holdShelfExpirationDate"])
    try:
        put_request(folio_client, request_to_put)
        print(
            f"PUT /circulation/requests/{request_to_put['id']} {json.dumps(request_to_put)}"
        )
        # patron = folio_client.folio_get_single_object(f"/users/{request_to_put['requesterId']}")
        # send_email(patron['personal']['email'])
        # send_email('support.lib@chalmers.se')
        # patron_emails_sucess.add(patron['personal']['email'])
    except Exception as ee:
        print(
            f"ERROR! PUT /circulation/loans/{request_to_put['id']} {json.dumps(request_to_put)}"
        )
        print(ee)
        traceback.print_exc()
        failed.add(request_to_put["requesterId"])
    i += 1
print(i)

print(patron_emails_sucess)
print(json.dumps(list(failed), indent=4))
