import os
import smtplib, ssl
from google.cloud import firestore
from google.cloud import secretmanager
client = firestore.Client()

def get_keys(key_names):
    project_id = os.environ["GCP_PROJECT"]
    client = secretmanager.SecretManagerServiceClient()
    keys = []

    for key_name in key_names:
        resource_name = f"projects/{project_id}/secrets/{key_name}/versions/latest"
        response = client.access_secret_version(resource_name)

        keys.append(response.payload.data.decode("UTF-8"))
    return keys

def mail_login(password):
    mail_context = ssl.create_default_context()
    port = int(os.environ["MAIL_PORT"])
    
    server = smtplib.SMTP_SSL(os.environ["MAIL_SERVER"], port, context=mail_context)
    try:
        server.login(os.environ["MAIL_ADDRESS"], password)
    except smtplib.SMTPException:
        return "Error logging into email"
    
    return server

keys = get_keys([os.environ["MAIL_PASSWORD_PATH"]])
mail_server = mail_login(keys[0])

def deliver_code(data, context):
    key = data["value"]["fields"]["name"]
    customer_email = data["value"]["fields"]["customer_email"]
    
    if mail_server is None:
        mail_server = mail_login(keys[0])
    
    message = """
        Subject: Your access key
        
        
        Hi """ + customer_email + """

        Your access key is """ + key + """


        Thanks,
        Volani Pay

        For support contact support@volani.co.uk
        """
    try:
        mail_server.sendmail(os.environ["MAIL_ADDRESS"], customer_email, message)
    except: 
        return 'Could not send email'
    return 'Email sent successfully'