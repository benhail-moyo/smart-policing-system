import os, smtplib
from dotenv import load_dotenv

load_dotenv('.env', override=True)
load_dotenv('backend/.env', override=True)

server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
port = int(os.getenv('SMTP_PORT', '587'))
username = os.getenv('SMTP_USERNAME', '').strip().replace(chr(34), '').replace(chr(39), '')
raw_pw = os.getenv('SMTP_PASSWORD', '')
password = ''.join(raw_pw.split()).replace(chr(34), '').replace(chr(39), '')

print('Testing connection with:')
print('  Server:', server)
print('  Port:', port)
print('  Username:', username)
print('  Password len:', len(password))

try:
    smtp = smtplib.SMTP(server, port, timeout=15)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(username, password)
    print('SUCCESS! SMTP authentication was successful!')
    smtp.quit()
except Exception as e:
    print('SMTP authentication failed:', e)
