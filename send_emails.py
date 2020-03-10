# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(from_email, to_emails, subject, content):
   
    message = Mail(
        from_email=from_email, #'from_email@example.com',
        to_emails=to_emails, #'to@example.com',
        subject=subject, #'Sending with Twilio SendGrid is Fun',
        html_content=content) #'<strong>and easy to do anywhere, even with Python</strong>')
    
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)

        return response.status_code

    except Exception as e:
        print(e.message)


if __name__ == '__main__':

    send_to_list = ['marymorg@broadinstitute.org']

    from_email = 'marymorg@broadinstitute.org'
    to_emails = ', '.join(send_to_list)
    subject = 'test subject'
    content = 'hello email world'


    send_email(from_email, to_emails, subject, content)