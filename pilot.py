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
            'date_sent': date_sent
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

def general_get_completion(client, messages):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_format={"type": "json_object"}
    )
    final_fields = None
    if completion.choices[0].message.content:
        final_fields = json.loads(completion.choices[0].message.content)
    else:
        print("No JSON object found in the text.")

    return completion, final_fields

# Update the function call
service = authenticate_gmail()


max_results = 3
query_string = f'(apply OR application OR applying)'
results = service.users().messages().list(
    userId='me',
    maxResults=max_results,
    labelIds=['INBOX'],
    q=f'{query_string} -category:promotions' # excludes promotions 
).execute()

# Process the results
emails = process_email_results(service, results)

email_content = ""
for email in emails:
    email_content += "----\n"
    email_content += f"email subject: {email['subject']}\n"
    email_content += f"email snippet: {email['snippet']}\n"

###### run emaiils through AI

"""
pass the email subject, snippet to an llm and ask it to 
a) deduce if it's about a job application
b) extract the company, and position type
c) output a json of email id, company name, position type
"""

client = OpenAI(api_key=os.environ.get("OPENAI_KEY"))

messages = [
    {"role": "system", "content": """You are a detail-oriented assistant reviewing emails to determine if they are from a company confirming they received my job application"""},
    {"role": "system", "content": """You are provided the email subject line as well as a preview of text from the email"""},
    {"role": "system", "content": """You have 2 tasks. A) determine if the email has to do with a job application. B) If it does, extract the company name and name of the position (if possible)"""},
    {"role": "system", "content": """return the output in json format"""},
    {"role": "user", "content": f"Here are the emails to review {email_content}"}
]

completion, final_fields = general_get_completion(client, messages)





######## archive


