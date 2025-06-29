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

def get_verification_code_from_email_gmail_api(timeout=60, exclude_codes=None, start_time=None):
    print("\nMengambil kode verifikasi dari Gmail API...")
    service = authenticate_gmail_api()
    if exclude_codes is None:
        exclude_codes = []
    if start_time is None:
        start_time = time.time() - 60  # fallback 1 menit ke belakang

    # Query untuk mencari email dari Instagram no-reply di kategori social
    query = 'from:no-reply@mail.instagram.com in:social newer_than:2h'
    max_retries = 6  # Maksimal 6 kali percobaan (30 detik total)
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"\nPercobaan {retry_count + 1}/{max_retries} mencari email verifikasi...")
            
            # Ambil daftar email
            results = service.users().messages().list(userId='me', q=query, maxResults=3).execute()
            messages = results.get('messages', [])
            
            if not messages:
                print("Belum ada email baru dari Instagram")
                retry_count += 1
                print(f"Menunggu 5 detik... ({retry_count}/{max_retries})")
                time.sleep(5)
                continue

            # Periksa setiap email
            for msg in messages:
                try:
                    msg_data = service.users().messages().get(userId='me', id=msg['id'], format='raw').execute()
                    msg_raw = base64.urlsafe_b64decode(msg_data['raw'].encode('ASCII'))
                    email_message = message_from_bytes(msg_raw)
                    
                    # Verifikasi pengirim
                    from_header = email_message.get('From', '')
                    if 'no-reply@mail.instagram.com' not in from_header:
                        continue
                    
                    email_timestamp = time.mktime(email.utils.parsedate(email_message['Date']))
                    if email_timestamp < start_time:
                        continue
                        
                    subject = email_message.get('Subject', '')
                    print(f"Memeriksa email dari: {from_header}")
                    print(f"Subject: {subject}")
                    print(f"Waktu email: {email_message.get('Date')}")
                    
                    # Cari kode di subject
                    match = re.search(r'\b(\d{6})\b', subject)
                    if match:
                        code = match.group(1)
                        if code not in exclude_codes:
                            print(f"Kode verifikasi ditemukan di subject: {code}")
                            return code

                    # Jika tidak ada di subject, cek body
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
                        if code not in exclude_codes:
                            print(f"Kode verifikasi ditemukan di body: {code}")
                            return code
                            
                except Exception as e:
                    print(f"Error saat memproses email: {e}")
                    continue
                    
            print("Tidak menemukan kode verifikasi di email yang ada")
            retry_count += 1
            if retry_count < max_retries:
                print(f"Menunggu 5 detik sebelum mencoba lagi... ({retry_count}/{max_retries})")
                time.sleep(5)
            
        except Exception as e:
            print(f"Error saat mengakses Gmail API: {e}")
            retry_count += 1
            if retry_count < max_retries:
                print(f"Menunggu 5 detik sebelum mencoba lagi... ({retry_count}/{max_retries})")
                time.sleep(5)
            
    print("\nBatas waktu habis setelah 30 detik!")
    print("Saran:")
    print("1. Pastikan email verifikasi sudah masuk ke Gmail")
    print("2. Pastikan email berada di kategori 'Social'")
    print("3. Pastikan email dikirim dari no-reply@mail.instagram.com")
    print("4. Coba cek spam folder jika tidak ada di Social")
    return None
