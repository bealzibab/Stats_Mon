import requests
import smtplib
from email.mime.text import MIMEText

def telegramAlert(token, chatID, message):
	url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chatID}&text={message}"
	print(requests.get(url).json())

def emailAlert(port, server, login, password, sender, reciever, text, subject)

	message = MIMEText(text, "plain")
	message["Subject"] = subject
	message["From"] = sender
	message["To"] = receiver

	with smtplib.SMTP(server, port) as server:
    	server.starttls()  # Secure the connection
    	server.login(login, password)
    	server.sendmail(sender, receiver, message.as_string())

