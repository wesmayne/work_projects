"""Check the status codes of all TMS Web Applications at a specified interval. 
If any are not available, send an error to TMS Support inbox
"""

import configparser
import smtplib
import requests

# read in config info
config = configparser.ConfigParser()
config.read(r"MyProjects\tms_status_check\tms.ini")

# read TMS URL from config
IGN_PROD = config["TMS"]["IGN_PROD"]
IGN_TEST = config["TMS"]["IGN_TEST"]
TNT_8081 = config["TMS"]["TNT_8081"]
TNT_PROD = config["TMS"]["TNT_PROD"]
TNT_TEST = config["TMS"]["TNT_TEST"]

# read email details from config
sender_email = config["EMAIL"]["sender_email"]
receiver_email = config["EMAIL"]["receiver_email"]
email_password = config["EMAIL"]["email_password"]

# TMS Web Applications
tms = {
    "Ignition Prod": IGN_PROD,
    "Ignition Test": IGN_TEST,
    "Track n Trace 8081": TNT_8081,
    "Track n Trace Prod": TNT_PROD,
    "Track n Trace Test": TNT_TEST,
}


def send_request():
    for key, value in tms.items():
        r = requests.get(value)
        if r.status_code != 300:
            error_email(key, value, r.status_code)


def error_email(key, value, code):
    message = (
        """Subject: TMS Error - Web Page Unavailable

    ***AUTOMATED EMAIL***\n\nTMS Web Page Unavailable\n\nWeb Page: """
        + str(key)
        + " "
        + str(value)
        + """\n\nHTTP Status Code: """
        + str(code)
    )

    mailserver = smtplib.SMTP("smtp.office365.com", 587)
    mailserver.ehlo()
    mailserver.starttls()
    mailserver.login(sender_email, email_password)
    mailserver.sendmail(sender_email, receiver_email, message)
    mailserver.quit()


"""  
try:
    send_request()
except:
    print('This is to cater for when smtp is down')
"""

