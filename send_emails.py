# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
import os
import argparse
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
    parser = argparse.ArgumentParser(description='')

    parser.add_argument('--from_email', type=str)
    parser.add_argument('--to_email', type=str)
    
    args = parser.parse_args()

    send_to_list = [args.to_email]
    from_email = args.from_email

    to_emails = ', '.join(send_to_list)
    subject = 'test subject'
    content = 'hello email world'

    response_code = send_email(from_email=from_email, to_emails=to_emails, subject=subject, content=content)

    if response_code == 202:
        print('Success! Email sent')