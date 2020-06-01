"""using SendGrid's Python Library
https://github.com/sendgrid/sendgrid-python"""
import os
import traceback
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

message = Mail(
    from_email="ellen.aberg@chalmers.se",
    to_emails="ttolstoy@ebsco.com",
    subject="Are you leaving Chalmers? Return your library books!",
    html_content='<p>Hej!</p><p>Slutar du på Chalmers? Kom ihåg att lämna tillbaka dina biblioteksböcker innan du lämnar oss. Bokinkastet är alltid öppet och du hittar det till vänster om huvudentrén till Huvudbiblioteket. Du kan även skicka böcker till oss med post:<br/>Chalmers tekniska högskolas bibliotek<br/>412 96 Göteborg</p><p>Chalmers bibliotek är stängda pga covid-19. Alla lån förlängs till biblioteken öppnar igen. </p><p><a href="http://www.lib.chalmers.se">http://www.lib.chalmers.se</a></p><hr/><p>Hi!</p><p>Are you leaving Chalmers? Don’t forget to return your library books before you leave us. The book drop is always open and you’ll find it at the left side of the main entrance at the Main library. You can also mail us your books:<br/>Chalmers tekniska högskolas bibliotek<br/>412 96 Göteborg</p><p>Chalmers libraries are closed due to covid-19. All loans are prolonged until the library opens again.</p><p><a href="http://www.lib.chalmers.se/en/">http://www.lib.chalmers.se/en/</a></p>',
)
try:
    print(os.environ.get("SENDGRID_API_KEY"))
    sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    response = sg.client.mail.send.post(request_body=message.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e)
    traceback.print_exc()
