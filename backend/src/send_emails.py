#!/usr/bin/python3

from time import gmtime, strftime, time

import smtplib

from ztdnslib import start_db_connection, get_ztdns_config

def sendMail(to, subject, content):

    email = 'FILL THIS FIELD'
    password = 'FILL THIS FIELD'
    message = 'Subject: {}\n\n{}'.format(subject, content)
    mail = smtplib.SMTP('smtp.gmail.com',587)
    mail.ehlo()
    mail.starttls()
    mail.login(email,password)
    mail.sendmail('zerotdns@gmail.com',to, message)
    mail.close()


config = get_ztdns_config()
if config['send_user_emails'] not in [True, 'yes']:
    print('Sending emails disabled in config - exiting')
    exit()

selectEmailsThatFailured = '''select distinct email from auth_user au
inner join user_side_subscription uss on au.id = uss.user_id
inner join user_side_service usservice on uss.service_id = usservice.id
inner join user_side_responses usr on usservice.id = usr.service_id
inner join user_side_response usr1 on usr.id = usr1.responses_id
where usr.result like 'successful' and usr1.returned_ip != usservice."IP" and
      usr.date = TIMESTAMP WITH TIME ZONE %s'''

connection = start_db_connection(config)
cursor = connection.cursor()

seconds = time()
seconds_hour_ago = seconds - 3600
timestamp_hour_ago = strftime('%Y-%m-%d %H:00%z', gmtime(seconds_hour_ago))

cursor.execute(selectEmailsThatFailured, (timestamp_hour_ago,))

content = 'Uwaga, DNS odpowiedział niepoprawnym adresem!'
# to = 'example@site.com'
subject = '0tdns alert'

for row in cursor.fetchall():
    to = row[0]
    if (to != ""):
        sendMail(to, subject, content)

cursor.close()
connection.close()

