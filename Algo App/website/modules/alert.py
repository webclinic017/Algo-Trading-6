import smtplib
from email.message import EmailMessage

def alert(subject,body,to):
    user = "sms.email.alerts1@gmail.com"
    password = "rwibitbdscsqghcm"
    
    msg = EmailMessage()
    msg.set_content(body)
    msg['subject'] = subject
    msg['to'] = to
    msg['from'] = user

    server = smtplib.SMTP("smtp.gmail.com",587)
    server.starttls()
    server.login(user,password)
    server.send_message(msg)
    server.quit()
