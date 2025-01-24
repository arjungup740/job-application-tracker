from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os
import datetime

# Authenticate Gmail API
def authenticate_gmail():
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    creds = None

    # Check if token.pickle exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials are available, request login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def process_email_results(service, results):
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = msg_data['payload']
        headers = payload['headers']
        thread_id = msg_data['threadId']

        # Extract subject
        subject = [header['value'] for header in headers if header['name'] == 'Subject'][0]

        # Extract sender
        sender = [header['value'] for header in headers if header['name'] == 'From'][0]

        ## Todo: get body extraction at some point, idk why it doesn't work

        # get date sent
        date_sent = datetime.datetime.fromtimestamp(int(msg_data['internalDate'])/1000).strftime('%Y-%m-%d %H:%M:%S')

        emails.append({
            'subject': subject,
            'sender': sender,
            # 'body': body,
            'snippet': msg_data['snippet'],
            'date_sent': date_sent,
            'thread_id': thread_id
        })

    return emails

service = authenticate_gmail()

max_results = 100  # You might want to increase this to get more emails
n_days = 1  # Number of days back to search

# Calculate the date n days ago
n_days_ago = datetime.date.today() - datetime.timedelta(days=n_days)

# Format the date for Gmail query
formatted_date = n_days_ago.strftime('%Y-%m-%d')
query_string = f'(application OR applying) after:{formatted_date}'
query_string = f'after:{formatted_date}' # api: 65 vs. ui: 53 + more in trash
query_string = f'(application OR applying)'
query_string = f'(application OR applying) AND after:{formatted_date}'

results = service.users().messages().list(
    userId='me',
    maxResults=max_results,
    # labelIds=['INBOX'],
    # includeSpamTrash=True,
    q=f'{query_string} '
).execute()
print(query_string)
len(results['messages'])
# Process the results
emails = process_email_results(service, results)
