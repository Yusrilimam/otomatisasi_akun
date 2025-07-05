import requests
import time

SMS_API_URL = "https://api.sms-activate.org/stubs/handler_api.php"

def get_phone_code(country_id):
    """Mendapatkan kode telepon berdasarkan ID negara."""
    # Ini adalah peta dari ID Negara ke Kode Telepon
    country_codes = {
        '73': '55',    # ID yang umum untuk Brazil
    }
    return country_codes.get(str(country_id))

def strip_country_code(full_number, phone_code):
    """Menghapus kode negara dari nomor telepon lengkap."""
    if full_number.startswith(phone_code):
        return full_number[len(phone_code):]
    elif full_number.startswith('+' + phone_code):
        return full_number[len(phone_code)+1:]
    else:
        return full_number.lstrip('+')

def request_phone_number(api_key, country_id, service='ig'):
    """Meminta nomor telepon dan memvalidasi negaranya."""
    print(f"Meminta nomor telepon untuk Negara ID: {country_id}...")
    params = {
        'api_key': api_key,
        'action': 'getNumber',
        'service': service,
        'country': country_id
    }

    expected_phone_code = get_phone_code(country_id)
    if not expected_phone_code:
        print(f" Error: Kode telepon untuk negara ID {country_id} tidak diketahui. Harap perbarui di sms_api_utils.py")
        return None, None

    try:
        response = requests.get(SMS_API_URL, params=params)
        response_text = response.text
        print(f"Respons dari API: {response_text}")

        if "ACCESS_NUMBER" in response_text:
            parts = response_text.split(':')
            activation_id = parts[1]
            phone_number_full = parts[2]
            if not phone_number_full.startswith(expected_phone_code):
                print(f" ERROR: Minta nomor negara ID {country_id} (kode: {expected_phone_code}), tapi dapat nomor dari negara lain ({phone_number_full}).")
                print("   -> Pastikan ID Negara di main.py sudah benar.")
                # Membatalkan aktivasi yang salah agar saldo tidak terpotong
                requests.get(SMS_API_URL, params={'api_key': api_key, 'action': 'setStatus', 'id': activation_id, 'status': 8})
                return None, None
            
            print(f" Nomor Brazil berhasil didapat & divalidasi! ID: {activation_id}, Nomor Lengkap: {phone_number_full}")
            return activation_id, phone_number_full
        else:
            print(f"Gagal mendapatkan nomor: {response_text}")
            return None, None
    except requests.RequestException as e:
        print(f"Error saat membuat permintaan API: {e}")
        return None, None

def get_sms_code(api_key, activation_id, max_wait_time=180):
    """Menunggu dan mengambil kode SMS yang masuk."""
    print(f"Menunggu kode SMS untuk ID: {activation_id}. Waktu tunggu maksimal: {max_wait_time} detik.")
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        params = {'api_key': api_key, 'action': 'getStatus', 'id': activation_id}
        try:
            response = requests.get(SMS_API_URL, params=params)
            response_text = response.text
            if "STATUS_OK" in response_text:
                code = response_text.split(':')[1]
                print(f"Kode SMS diterima: {code}")
                return code
            elif "STATUS_WAIT_CODE" not in response_text:
                print(f"Terjadi error atau status tak terduga: {response_text}")
                return None
            time.sleep(10)
        except requests.RequestException as e:
            print(f"Error saat mengecek status API: {e}")
            time.sleep(10)
    
    print("Gagal mendapatkan kode SMS dalam waktu yang ditentukan.")
    return None
