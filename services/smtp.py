import os
import smtplib
from email.message import EmailMessage

class SMTP:
    _server = smtplib.SMTP('smtp.gmail.com', 587)
    _server.starttls()
    _server.login('map.admin@f3nation.com', 'Wxa74L9Bcp^B^pFe')
    
    def send_email(self, subject: str, toEmails: list, body: str) -> None:

        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = 'maps-admins@f3nation.com'
        message['To'] = ', '.join(toEmails)
        message.set_content(body, subtype='html')

        self._server.send_message(message)