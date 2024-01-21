import os
import smtplib
import ssl
from email.message import EmailMessage

class SMTP:
    _EMAIL_ACCOUNT = os.getenv('EMAIL_ACCOUNT')
    _EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    _EMAIL_FROM_ADDRESS = os.getenv('EMAIL_FROM_ADDRESS')

    
    def send_email(self, subject: str, toEmails: list, body: str) -> None:

        context = ssl.create_default_context()

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls(context=context)
        server.login(self._EMAIL_ACCOUNT, self._EMAIL_PASSWORD)

        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = self._EMAIL_FROM_ADDRESS
        message['To'] = ', '.join(toEmails)
        message.set_content(body, subtype='html')

        server.send_message(message)

        server.close()