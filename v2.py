from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os
import datetime
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()


def pretty_print_dict_preview(d, num_entries=10):
    """Print the first few entries of a dictionary in a readable format."""
    print("\nDictionary Preview:")
    print("-" * 40)
    for i, (key, value) in enumerate(d.items()):
        if i >= num_entries:
            break
        print(f"{key}: {value}")
    remaining = len(d) - num_entries
    if remaining > 0:
        print(f"... and {remaining} more entries")
    print("-" * 40)


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

def extract_json(text):
    """
    Extracts the JSON object from a text containing commentary and JSON content.

    Parameters:
        text (str): The input text containing commentary and a JSON object.

    Returns:
        dict: The extracted JSON object as a Python dictionary.
    """
    # Use regex to match a JSON-like structure
    json_match = re.search(r"\{.*?\}", text, re.DOTALL)
    
    if json_match:
        json_string = json_match.group()
        try:
            # Parse the JSON string into a dictionary
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)
            return None
    else:
        print("No JSON object found in the text.")
        return None


def get_thread_messages(client, thread):

    messages_cursor = client.beta.threads.messages.list(thread_id=thread.id)
    messages = [message for message in messages_cursor]
    res_txt = messages[0].content[0].text.value

    if res_txt:
       parsed_json = extract_json(res_txt)
    else:
        print("No JSON object found in the text.")
        parsed_json = None

    return messages, parsed_json

def general_get_completion(client, messages, require_json=False):
    # Set up completion parameters
    params = {
        "model": "gpt-4o-mini",
        "messages": messages
    }
    
    # Add response format parameter only if JSON is required
    if require_json:
        params["response_format"] = {"type": "json_object"}
    
    completion = client.chat.completions.create(**params)
    
    # Handle the response
    content = completion.choices[0].message.content
    if require_json:
        try:
            return completion, json.loads(content) if content else None
        except json.JSONDecodeError:
            print("Error: Response was not valid JSON")
            return completion, None
    
    return completion, content

# Update the function call
service = authenticate_gmail()


max_results = 100  # You might want to increase this to get more emails
n_days = 1  # Number of days back to search

# Calculate the date n days ago
n_days_ago = datetime.date.today() - datetime.timedelta(days=n_days)

# Format the date for Gmail query
formatted_date = n_days_ago.strftime('%Y-%m-%d')
query_string = f'(application OR applying) after:{formatted_date}'

results = service.users().messages().list(
    userId='me',
    maxResults=max_results,
    labelIds=['INBOX'],
    q=f'{query_string} -category:promotions'
).execute()
# Process the results
emails = process_email_results(service, results)

email_content = ""
for email in emails:
    email_content += "----\n"
    email_content += f"email subject: {email['subject']}\n"
    email_content += f"email snippet: {email['snippet']}\n"
    email_content += f"thread id: {email['thread_id']}\n"

###### run emaiils through AI

openai_client = OpenAI(api_key=os.environ.get("OPENAI_KEY"))

one_llm_pass = False # one pass, or multple?

if not one_llm_pass:
    """
    1st step: determine if it has to do with a job application, offer to apply, rejection, etc. Something job related
        * if not job related, ignore
        * pass in the subject, snipped and thread id, return thread ids
    2nd step: if it is job related, extract the from, company name, position, type (receipt, rejection , offer, etc)
    """
    messages = [
        {"role": "system", "content": """You are a detail-oriented assistant reviewing emails to determine if they have to do with a job application -- a job application is any email that has to do with applying for a job"""},
        {"role": "system", "content": """You are provided the email subject line as well as a preview of text from the email as well as an alphanumeric thread_id which is unique to each email"""},
        {"role": "system", "content": """Your job is to determine if the email has to do with a job application. If it does, output a list of thread ids in python list format (e.g. ['123', '456', '789']). DO NOT include the word 'python' in your output"""},
        {"role": "user", "content": f"Here are the emails to review: {email_content}"}
]

    completion, content = general_get_completion(openai_client, messages)


if one_llm_pass:
    """
    pass the email subject, snippet to an llm and ask it to 
    a) deduce if it's about a job application
    b) extract the company, and position type
    c) output a json of email id, company name, position type
    """
    messages = [
        {"role": "system", "content": """You are a detail-oriented assistant reviewing emails to determine if they are from a company confirming they received my job application"""},
        {"role": "system", "content": """You are provided the email subject line as well as a preview of text from the email"""},
        {"role": "system", "content": """You have 2 tasks. A) determine if the email has to do with a job application. B) If it does, extract the company name and name of the position (if possible)"""},
        {"role": "system", "content": """If the email is not about a job, ignore it. If the email is about a job, output a csv with the following: date_sent, company, position, notes. These should be the only 4 columns"""},
        {"role": "system", "content": """In the position column, things like 'Data Scientist, Product' are part of the position. Do not break out 'Data Scientist' from 'Product' in these scenarios."""},
        {"role": "system", "content": """In the notes column, if the email is a rejection, put 'rejection'. If it is confirmation of receipt of an application ('thanks for applying', 'we received your application' etc.) put 'receipt'. 
                                        If it is an offer of a job, a listing, or invitation to apply, put 'listing' """},
        {"role": "user", "content": f"Here are the emails to review: {email_content}"}
]

    completion, content = general_get_completion(openai_client, messages)

# Extract CSV content and convert to pandas DataFrame

# Split the content into lines and remove markdown formatting
csv_content = content.strip().split('\n')[1:]  # Skip the ```csv header
csv_data = [line.split(',') for line in csv_content if line and not line.startswith('```')]

# Create DataFrame
# df = pd.DataFrame(csv_data, columns=['company', 'position'])
df = pd.DataFrame(csv_data)

########## Write to sheet. 

# Google Sheets Integration
SCOPE = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
CREDS = ServiceAccountCredentials.from_json_keyfile_name(
    'email-jobs-manager-service-account-creds.json', SCOPE)  # Replace with your credentials file
SPREADSHEET_NAME = "Job Application Tracking"

g_client = gspread.authorize(CREDS)
sheet = g_client.open(SPREADSHEET_NAME).sheet1

# Choose append or overwrite
append_data = True  # Set to False to overwrite

if append_data:
    # Append data to the sheet
    sheet.append_rows(df.values.tolist(), value_input_option='USER_ENTERED')
else:
    # Clear existing data and write DataFrame
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())



######## scratch


msg_data = service.users().messages().get(userId='me', id='19492d33b568351c').execute()


