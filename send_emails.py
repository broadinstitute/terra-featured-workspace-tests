# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(from_email, to_emails, subject, content):
    message = Mail(
        from_email=from_email, 
        to_emails=to_emails, 
        subject=subject, 
        html_content=content) 
    
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)

        return response.status_code

    except Exception as e:
        print(e)
        return e


if __name__ == '__main__':

    send_to_list = ['your-email-here']

    from_email = 'terra-support-sendgrid@broadinstitute.org'
    to_emails = ', '.join(send_to_list)
    subject = 'test subject'
    content = 'hello email world'


    response_code = send_email(from_email=from_email, to_emails=to_emails, subject=subject, content=content)

    if response_code == 202:
        print('Success! Email sent')