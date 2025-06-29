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

    # Query untuk mencari email dari Instagram no-reply
    query = 'from:no-reply@mail.instagram.com is:unread newer_than:2m'
    max_retries = 6
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"\nPercobaan {retry_count + 1}/{max_retries} mencari email verifikasi...")
            
            # Ambil daftar email dan urutkan berdasarkan internal date
            results = service.users().messages().list(
                userId='me', 
                q=query,
                maxResults=10,
                orderBy='internalDate'
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print("Belum ada email baru dari Instagram")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Menunggu 5 detik... ({retry_count}/{max_retries})")
                    time.sleep(5)
                continue

            # Ambil detail untuk setiap email dan urutkan berdasarkan timestamp
            detailed_messages = []
            for msg in messages:
                try:
                    msg_detail = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Ambil timestamp internal dari email
                    internal_date = int(msg_detail['internalDate']) / 1000  # Convert to seconds
                    
                    if internal_date > start_time:
                        headers = msg_detail['payload']['headers']
                        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
                        from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
                        date_header = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
                        
                        detailed_messages.append({
                            'id': msg['id'],
                            'timestamp': internal_date,
                            'subject': subject,
                            'from': from_header,
                            'date': date_header,
                            'detail': msg_detail
                        })
                except Exception as e:
                    print(f"Error saat memproses email: {e}")
                    continue

            # Urutkan email berdasarkan timestamp, ambil yang terbaru
            if detailed_messages:
                detailed_messages.sort(key=lambda x: x['timestamp'], reverse=True)
                newest_message = detailed_messages[0]
                
                print(f"\nMemeriksa email terbaru:")
                print(f"Dari: {newest_message['from']}")
                print(f"Subject: {newest_message['subject']}")
                print(f"Tanggal: {newest_message['date']}")
                print(f"Timestamp Internal: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(newest_message['timestamp']))}")
                
                # Cari kode di subject
                match = re.search(r'\b(\d{6})\b', newest_message['subject'])
                if match:
                    code = match.group(1)
                    if code not in exclude_codes:
                        print(f"Kode verifikasi ditemukan di subject: {code}")
                        
                        # Tandai email sebagai sudah dibaca
                        service.users().messages().modify(
                            userId='me',
                            id=newest_message['id'],
                            body={'removeLabelIds': ['UNREAD']}
                        ).execute()
                        
                        return code

                # Jika tidak ada di subject, cek body
                msg_data = newest_message['detail']
                if 'data' in msg_data['payload'].get('body', {}):
                    body = base64.urlsafe_b64decode(msg_data['payload']['body']['data']).decode('utf-8')
                else:
                    # Handle multipart messages
                    parts = msg_data['payload'].get('parts', [])
                    body = ""
                    for part in parts:
                        if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            break

                match = re.search(r'\b(\d{6})\b', body)
                if match:
                    code = match.group(1)
                    if code not in exclude_codes:
                        print(f"Kode verifikasi ditemukan di body: {code}")
                        
                        # Tandai email sebagai sudah dibaca
                        service.users().messages().modify(
                            userId='me',
                            id=newest_message['id'],
                            body={'removeLabelIds': ['UNREAD']}
                        ).execute()
                        
                        return code
            
            print("Tidak menemukan kode verifikasi di email terbaru")
            retry_count += 1
            if retry_count < max_retries:
                print(f"Menunggu 5 detik... ({retry_count}/{max_retries})")
                time.sleep(5)
            
        except Exception as e:
            print(f"Error saat mengakses Gmail API: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                print(f"Menunggu 5 detik... ({retry_count}/{max_retries})")
                time.sleep(5)
            
    print("\nBatas waktu habis!")
    print("Saran:")
    print("1. Pastikan email verifikasi sudah masuk ke Gmail")
    print("2. Pastikan email dikirim dari no-reply@mail.instagram.com")
    print("3. Coba request kode verifikasi baru")
    return None
