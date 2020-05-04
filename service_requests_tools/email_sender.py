"""using SendGrid's Python Library
https://github.com/sendgrid/sendgrid-python"""
import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

message = Mail(
    from_email='support.lib@chalmers.se',
    to_emails='ttolstoy@ebsco.com',
    subject='Ändrade återlämningsdatum. Chalmers bibliotek har stängt till vidare med anledning av Covid-19 / Changed due dates. Chalmers libraries are closed due to Covid-19',
    html_content='<p><strong>Hej!</strong></p><p>Alla Chalmers bibliotek har st&auml;ngt tills vidare med anledning av Covid-19, fr&aring;n 18 mars och fram&aring;t. Om du har p&aring;g&aring;ende l&aring;n flyttar vi automatiskt fram &aring;terl&auml;mningsdatum under tiden vi har st&auml;ngt, s&aring; att du inte beh&ouml;ver komma till biblioteket med dina b&ouml;cker. Vill man &auml;nd&aring; &aring;terl&auml;mna b&ouml;cker kan man g&ouml;ra det i bokinkastet vid Huvudbibliotekets entr&eacute;.</p><p>Utl&aring;n och reservationer av b&ouml;cker &auml;r inte m&ouml;jlig under den st&auml;ngda perioden, men du kommer &aring;t bibliotekets e-resurser (e-b&ouml;cker, e-tidskrifter, databaser) som vanligt.</p><p>Mer information finns att l&auml;sa p&aring; bibliotekets webbplats <a href="http://lib.chalmers.se">http://lib.chalmers.se.</a> Vi hj&auml;lper dig g&auml;rna med olika fr&aring;gor via v&aring;r email-support eller via telefon.</p><p>V&auml;nliga h&auml;lsningar,<br />Chalmers bibliotek</p><p>Huvudbiblioteket<br />Visiting address: H&ouml;rsalsv&auml;gen 2<br />Email: <a href="mailto:support.lib@chalmers.se">support.lib@chalmers.se</a><br />Phone: 031-772 37 37</p><p>&nbsp;</p><p>-------------English version---------------</p><p><strong>Hi,&nbsp;</strong></p><p>From March 18 until further notice all Chalmers libraries will be completely closed to visitors. Ongoing loans will be automatically extended with a new due date. You don&rsquo;t have to bring your borrowed books back, but if you need to you can return them in the book drop at the entrance of the Main library. It&rsquo;s not possible to request or borrow printed books during this closed period. E-books, e-journals and databases will be accessible as usual.</p><p>Find more information at the library web site <a href="http://lib.chalmers.se/en">http://lib.chalmers.se/en.</a> We`ll be happy to answer any questions you might have. Contact information below.</p><p>Best regards,<br />Chalmers Library</p><p>Main Library<br />Visiting address: H&ouml;rsalsv&auml;gen 2<br />Email: <a href="mailto:support.lib@chalmers.se">support.lib@chalmers.se</a><br />Phone: 031-772 37 37</p><p>&nbsp;</p>')
try:
    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e)
