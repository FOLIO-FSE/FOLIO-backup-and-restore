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
        from_email='support.lib@chalmers.se',
        to_emails=email_address,
        subject='Ändrade återlämningsdatum. Chalmers bibliotek har stängt till vidare med anledning av Covid-19 / Changed due dates. Chalmers libraries are closed due to Covid-19',
        html_content='<p><strong>Hej!</strong></p><p>Alla Chalmers bibliotek har st&auml;ngt tills vidare med anledning av Covid-19, fr&aring;n 18 mars och fram&aring;t. Om du har p&aring;g&aring;ende l&aring;n flyttar vi automatiskt fram &aring;terl&auml;mningsdatum under tiden vi har st&auml;ngt, s&aring; att du inte beh&ouml;ver komma till biblioteket med dina b&ouml;cker. Vill man &auml;nd&aring; &aring;terl&auml;mna b&ouml;cker kan man g&ouml;ra det i bokinkastet vid Huvudbibliotekets entr&eacute;.</p><p>Utl&aring;n och reservationer av b&ouml;cker &auml;r inte m&ouml;jlig under den st&auml;ngda perioden, men du kommer &aring;t bibliotekets e-resurser (e-b&ouml;cker, e-tidskrifter, databaser) som vanligt.</p><p>Mer information finns att l&auml;sa p&aring; bibliotekets webbplats <a href="http://lib.chalmers.se">http://lib.chalmers.se.</a> Vi hj&auml;lper dig g&auml;rna med olika fr&aring;gor via v&aring;r email-support eller via telefon.</p><p>V&auml;nliga h&auml;lsningar,<br />Chalmers bibliotek</p><p>Huvudbiblioteket<br />Visiting address: H&ouml;rsalsv&auml;gen 2<br />Email: <a href="mailto:support.lib@chalmers.se">support.lib@chalmers.se</a><br />Phone: 031-772 37 37</p><p>&nbsp;</p><p>-------------English version---------------</p><p><strong>Hi,&nbsp;</strong></p><p>From March 18 until further notice all Chalmers libraries will be completely closed to visitors. Ongoing loans will be automatically extended with a new due date. You don&rsquo;t have to bring your borrowed books back, but if you need to you can return them in the book drop at the entrance of the Main library. It&rsquo;s not possible to request or borrow printed books during this closed period. E-books, e-journals and databases will be accessible as usual.</p><p>Find more information at the library web site <a href="http://lib.chalmers.se/en">http://lib.chalmers.se/en.</a> We`ll be happy to answer any questions you might have. Contact information below.</p><p>Best regards,<br />Chalmers Library</p><p>Main Library<br />Visiting address: H&ouml;rsalsv&auml;gen 2<br />Email: <a href="mailto:support.lib@chalmers.se">support.lib@chalmers.se</a><br />Phone: 031-772 37 37</p><p>&nbsp;</p>')
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
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
    path1 = '/circulation/loans'
    query = '?query=(status.name="Open")' 
    print(f"path: {path1} query: {query}")    
    loans = folio_client.folio_get_all(path1, 'loans', query)
    print(f"fetched {len(loans)} loans")
    return loans


def get_user_emails(folio_client, user_ids):
    i = 0
    for user_id in user_ids:
        i+=1
        try:
            patron = folio_client.folio_get_single_object(f"/users/{user_id}")
            yield patron['personal']['email']
        except Exception as ee:
            print(ee)
            traceback.print_exc()
            raise ee
        if i%10 == 0:
            print(i)


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
print(f'{args.tenant_id} {args.username} {args.okapi_url}')
folio_client = FolioClient(args.okapi_url, args.tenant_id, args.username,
                           args.password)

patron_emails = set()
i = 0
loans = get_all_open_loans(folio_client)
user_ids = list(set([l["userId"] for l in loans]))[182:]
print(len(user_ids))
patron_emails = list(set(get_user_emails(folio_client, user_ids)))
print(len(patron_emails))
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