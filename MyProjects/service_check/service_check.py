"""Check the status of TMS services on remote servers, select an action to apply to the service,
then return results via email
"""
import win32serviceutil
import configparser
import smtplib
import json

# read in json dicts
with open(r"MyProjects\service_check\service.json") as f:
    service_json = json.load(f)

test_services_dict = service_json["test"]
prod_services_dict = service_json["prod"]

# read in config details
config = configparser.ConfigParser()
config.read(r'MyProjects\service_check\service.ini')

# read in config variables
env = config['DETAILS']['env']
action = config['DETAILS']['action']
sender_email = config['EMAIL']['sender_email']
receiver_email = config['EMAIL']['receiver_email']
email_password = config['EMAIL']['email_password']

# initialise message details for later use
active = []
inactive = []
message = ''

def service_running(service, machine):
    return win32serviceutil.QueryServiceStatus(service, machine)[1] == 4

def service_info(action, machine, service):
    running = service_running(service, machine)
    servnam = f'service {service} on machine {machine}'
    action = action.lower()

    if action == 'stop':
        if not running:
            inactive.append(service)
            print (f"Can't stop, {servnam} not running")
            return 0
        win32serviceutil.StopService(service, machine)
        if running:
            print (f"Can't stop {servnam} (???)")
            active.append(service)
            return 0
        print (f'{servnam} stopped successfully')
        inactive.append(service)


    elif action == 'start':
        if running:
            print (f"Can't start, {servnam} already running")
            active.append(service)
            return 0
        win32serviceutil.StartService(service, machine)
        if not running:
            print (f"Can't start {servnam} (???)")
            inactive.append(service)
            return 0
        print (f'{servnam} started successfully')
        active.append(service)
    

    elif action == 'restart':
        if not running:
            inactive.append(service)
            return 0
        win32serviceutil.RestartService(service, machine)
        if not running:
            inactive.append(service)
            print (f"Can't restart {servnam} (???)")
            return 0
        active.append(service)
        print (f'{servnam} restarted successfully')
    

    elif action == 'status':
        if not running:
            inactive.append(service)
        else:
            active.append(service)
    else:
        return 0

def sendmail(sender_email, receiver_email, email_password, message):

    # email message
    message = f'''Subject: TMS Service Status\n\nAfter execution of action: '{action}' in environment: '{env}'
    \n\nThe below services are now active: \n{active}
    \n\nThe below services are now inactive: \n{inactive}
    '''
    # manages a connection to an SMTP server
    server = smtplib.SMTP(host="smtp.gmail.com", port=587)
    # connect to the SMTP server as TLS mode ( for security )
    server.starttls()
    # login to the email account
    server.login(sender_email, email_password)
    # send the actual message
    server.sendmail(sender_email, receiver_email, message)
    # terminates the session
    server.quit()


if env == 'test':
    for service, machine in test_services_dict.items():
        service_info(action, machine, service)
    sendmail(sender_email, receiver_email, email_password, message)

elif env == 'prod':
    for service, machine in prod_services_dict.items():
        service_info(action, machine, service)
    sendmail(sender_email, receiver_email, email_password, message)
