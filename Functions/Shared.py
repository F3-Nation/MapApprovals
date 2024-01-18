import smtplib
from email.message import EmailMessage

# Email
def send_email(subject: str, toEmails: list, body: str) -> None:
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.starttls()
    smtp.login('map.admin@f3nation.com', 'Wxa74L9Bcp^B^pFe')

    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = 'maps-admins@f3nation.com'
    message['To'] = ', '.join(toEmails)
    message.set_content(body, subtype='html')

    smtp.send_message(message)