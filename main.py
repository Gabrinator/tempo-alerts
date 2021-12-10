import os
from  datetime import date

import boto3
from botocore.exceptions import ClientError
import pandas as pd
from tempoapiclient import client


tempo = client.Tempo(
    auth_token=os.environ['TEMPO_API_TOKEN'],
    base_url="https://api.tempo.io/core/3")

projects = pd.read_excel('projects.xlsx')

def calculate_total_time(project_key, date_from, date_to=str(date.today())):
    worklogs = tempo.get_worklogs(
        dateFrom=date_from,
        dateTo=date_to,
        projectKey=project_key
        )

    total_time_spent = 0 #in seconds

    for i in worklogs:
        total_time_spent += i["timeSpentSeconds"]

    return total_time_spent/3600 #convert to hours

def send_notification(sender,  recipient, aws_region, subject, body_text, body_html=None):

    # This address must be verified with Amazon SES.
    sender = "Alerts <alerts@gabrielfrechette.com>"

    # Replace recipient@example.com with a "To" address. If your account 
    # is still in the sandbox, this address must be verified.
    recipient = "gabriel.frechette@novadba.com"

    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the 
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    #CONFIGURATION_SET = "ConfigSet"

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    aws_region = "ca-central-1"

    # The subject line for the email.
    subject = "Amazon SES Test (SDK for Python)"

    # The email body for recipients with non-HTML email clients.
    body_text = ("Amazon SES Test (Python)\r\n"
                "This email was sent with Amazon SES using the "
                "AWS SDK for Python (Boto)."
                )
                
    # The HTML body of the email.
    body_html = """<html>
    <head></head>
    <body>
    <h1>Amazon SES Test (SDK for Python)</h1>
    <p>This email was sent with
        <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
        <a href='https://aws.amazon.com/sdk-for-python/'>
        AWS SDK for Python (Boto)</a>.</p>
    </body>
    </html>
                """            

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=aws_region)

    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    recipient,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': body_html,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': body_text,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': subject,
                },
            },
            Source=sender,
            # If you are not using a configuration set, comment or delete the
            # following line
            #ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

def generate_email_body(projects_over_limit):
    email_body_html = """<html>
    <head></head>
    <body>
    <p>The following projects have reached the threshold:
    <ul>
    """

    for p in projects_over_limit:
        email_body_html += '<li>' + p + '</li>'

    email_body_html+= """
    </ul>
    </p>
    <p>Take action now.</p>
    </body>
    </html>
    """

    body_text = f"The following projects have reached the threshold: {str.join(', ', projects_over_limit)}  " 
    
    return email_body_html, body_text

def get_time_limit(project):
    limit = min(projects[projects["Project"] ==  project]["Time Limit"]) #min prevents errors when duplicate projects
    return limit

projects_to_monitor= projects['Project']

#pproaching_limit = []
exceeded_limit  = []

for p in projects_to_monitor:
    tot_time = calculate_total_time(p, "2021-12-01")
    time_limit = get_time_limit(p)
    if tot_time > time_limit:
        exceeded_limit.append(p)
    projects.loc[(projects['Project'] == p),'Time Logged'] = tot_time

projects.to_excel('projects.xlsx', index=False)

body_html, body_text  = generate_email_body(exceeded_limit)

print(body_text)
