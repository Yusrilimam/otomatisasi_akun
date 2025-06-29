import os
import base64
import time
import re
import email
from email import message_from_bytes
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail_api():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

def get_verification_code_from_email_gmail_api(timeout=120, exclude_codes=None, start_time=None):
    print("Mengambil kode verifikasi dari Gmail API...")
    service = authenticate_gmail_api()
    if exclude_codes is None:
        exclude_codes = []
    if start_time is None:
        start_time = time.time() - 60  # fallback 1 menit ke belakang

    query = 'from:instagram newer_than:1d'
    polling_start = time.time()
    while time.time() - polling_start < timeout:
        try:
            results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
            messages = results.get('messages', [])
            for msg in messages:
                msg_data = service.users().messages().get(userId='me', id=msg['id'], format='raw').execute()
                msg_raw = base64.urlsafe_b64decode(msg_data['raw'].encode('ASCII'))
                email_message = message_from_bytes(msg_raw)
                email_timestamp = time.mktime(email.utils.parsedate(email_message['Date']))
                if email_timestamp < start_time:
                    continue
                subject = email_message.get('Subject', '')
                match = re.search(r'\b(\d{6})\b', subject)
                if match:
                    code = match.group(1)
                    if code in exclude_codes:
                        continue
                    print(f"Kode verifikasi ditemukan di subject: {code}")
                    return code
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                match = re.search(r'\b(\d{6})\b', body)
                if match:
                    code = match.group(1)
                    if code in exclude_codes:
                        continue
                    print(f"Kode verifikasi ditemukan di body: {code}")
                    return code
        except Exception as e:
            print(f"Error Gmail API: {e}")
        print("Kode verifikasi belum ditemukan, menunggu 5 detik...")
        time.sleep(5)
    print("Timeout: Tidak menemukan kode verifikasi baru!")
    return None
