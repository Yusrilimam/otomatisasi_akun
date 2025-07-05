import os, string, requests
import subprocess
import time
from datetime import datetime, timezone
import uiautomator2 as u2
import uuid
import random
from sms_api_utils import (
    request_phone_number,
    get_phone_code,
    strip_country_code,
    get_sms_code,
)
    
# KONFIGURASI PATH DAN DEVICE UNTUK LDPLAYER
LDPLAYER_EXE_PATH = r"C:\LDPlayer\LDPlayer9\dnplayer.exe"
ADB_PATH = r"C:\LDPlayer\LDPlayer9\adb.exe"
LDPLAYER_DEVICE = "emulator-5554"
APK_PATH = r"C:\xampp\htdocs\otomatisai_akun\instagram-lite-466-0-0-9-106.apk"  
API_KEY = "9d3fc401fB8665790fd1dfB167547e92"
ID_NEGARA = 73 

# --- FUNGSI-FUNGSI HELPER ---

def check_current_ip():
    """Mengecek dan menampilkan alamat IP publik saat ini."""
    print("\n Mengecek alamat IP publik saat ini...")
    try:
        # Menggunakan layanan eksternal untuk mendapatkan IP
        response = requests.get('https://api.ipify.org?format=json', timeout=10)
        response.raise_for_status()  # Cek jika ada error HTTP
        ip_address = response.json()['ip']
        print(f"✅ IP Publik saat ini adalah: {ip_address}")
        return ip_address
    except requests.exceptions.RequestException as e:
        print(f"❌ Gagal mengecek IP: {e}")
        return None

def generate_random_fullname(length=10):
    chars = string.ascii_lowercase + string.digits
    return 'JaWa' + ''.join(random.choices(chars, k=length))

def generate_random_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=length))

def connect_device():
    d = u2.connect(LDPLAYER_DEVICE)
    print('Terhubung dengan device:', d.info)
    return d

def start_ldplayer_and_connect_adb():
    global LDPLAYER_DEVICE
    print("Menjalankan emulator LDPlayer...")
    out = subprocess.getoutput(f'"{ADB_PATH}" devices')
    if "device" in out and LDPLAYER_DEVICE in out:
        print("Emulator sudah berjalan dan terhubung.")
        return

    subprocess.Popen([LDPLAYER_EXE_PATH])
    max_wait = 180
    wait_time = 0
    while wait_time < max_wait:
        out = subprocess.getoutput(f'"{ADB_PATH}" devices')
        device_list = [line for line in out.splitlines() if "device" in line and "List" not in line]
        if device_list:
            device_line = device_list[0]
            print(f"Emulator siap, adb terhubung sebagai: {device_line.strip()}")
            LDPLAYER_DEVICE = device_line.split()[0]
            return
        print("Menunggu koneksi ADB...")
        time.sleep(5)
        wait_time += 5
    raise RuntimeError("Gagal mendapatkan koneksi ADB ke emulator dalam 3 menit!")

def unlock_screen():
    os.system(f'"{ADB_PATH}" -s {LDPLAYER_DEVICE} shell input keyevent 224 && "{ADB_PATH}" -s {LDPLAYER_DEVICE} shell input keyevent 82')

def handle_permission_popup(d):
    """Menangani dialog izin awal dengan memprioritaskan 'ALLOW'."""
    print("\nMemeriksa dialog izin awal...")
    
    # Prioritas 1: Mencari tombol 'ALLOW' berdasarkan resource-id standar Android
    allow_button_id = "com.android.permissioncontroller:id/permission_allow_button"
    if d(resourceId=allow_button_id).wait(timeout=10):
        d(resourceId=allow_button_id).click()
        print("Izin diklik via resourceId.")
        return

    # Prioritas 2: Mencari tombol 'ALLOW' berdasarkan teks (sebagai fallback)
    if d(text="ALLOW").wait(timeout=2):
        d(text="ALLOW").click()
        print(" Izin diklik via teks.")
        return
        
    print("-> Tidak ada dialog izin yang terdeteksi.")

def set_birthday(d, min_age=18, max_age=30):
    def save_xml_to_file(d, prefix):
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"birthday_page_{prefix}_{timestamp}.xml"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(d.dump_hierarchy())
            print(f"Saved page inspection to {filename}")
        except Exception as e:
            print(f"Gagal menyimpan XML: {e}")

    print("\nStarting birthday setup process...")
    time.sleep(3)

    # --- LANGKAH 1: Klik tombol Next di halaman Add your birthday ---
    print("\nLangkah 1: Mengklik tombol Next...")
    xpath_next = '//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[3]'
    
    if d.xpath(xpath_next).exists:
        d.xpath(xpath_next).click()
        print("Tombol Next berhasil diklik")
        time.sleep(2)
    else:
        print("Gagal menemukan tombol Next!")
        return False

    # --- LANGKAH 2: Menangani popup 'Enter your real birthday' ---
    print("\nLangkah 2: Menangani popup birthday...")
    time.sleep(2)

    # Klik OK di popup
    try:
        d.click(430, 840)  # Koordinat tengah
        print("Klik koordinat tengah untuk popup")
        time.sleep(1)
        d.click(450, 850)  # Koordinat OK
        print("Klik koordinat tombol OK")
    except Exception as e:
        print(f"Gagal klik popup: {e}")
        return False

    time.sleep(2)

    # --- LANGKAH 3: Klik tombol "Enter age instead" ---
    print("\nLangkah 3: Mencari dan mengklik tombol 'Enter age instead'...")
    
    # Coba klik menggunakan koordinat yang tepat dari XML
    try:
        d.click(354, 1481)  # Titik tengah dari bounds="[354,1481][546,1510]"
        print("Enter age instead diklik via koordinat yang tepat")
        time.sleep(3)
    except Exception as e:
        print(f"Gagal klik Enter age instead via koordinat: {e}")
        return False

    # Verifikasi halaman Enter your age muncul
    time.sleep(2)

    # Cek field input
    if not d(className="android.widget.MultiAutoCompleteTextView").exists:
        print("Halaman Enter your age tidak terdeteksi!")
        return False
    
    print("Halaman Enter your age terdeteksi")

    # --- LANGKAH 4: Mengisi field age ---
    print("\nLangkah 4: Mengisi field age...")
    age = str(random.randint(min_age, max_age))
    
    input_field = d(className="android.widget.MultiAutoCompleteTextView")
    if input_field.exists:
        try:
            input_field.click()
            time.sleep(1)
            input_field.set_text(age)
            print(f"Berhasil mengisi usia: {age}")
        except Exception as e:
            print(f"Gagal mengisi age: {e}")
            return False
    else:
        print("Field age tidak ditemukan!")
        return False

    time.sleep(2)

    # --- LANGKAH 5: Klik Next final ---
    print("\nLangkah 5: Klik Next final...")
    try:
        # Menggunakan koordinat dari bounds="[30,385][870,451]"
        d.click(425, 404)  # Titik tengah dari bounds Next button
        print("Next final diklik via koordinat")
        time.sleep(2)
        
        # Verifikasi tambahan - coba klik sekali lagi jika masih di halaman yang sama
        if d(className="android.widget.MultiAutoCompleteTextView").exists:
            d.click(450, 418)  # Coba klik lagi
            print("Mencoba klik Next lagi")
            time.sleep(2)
    except Exception as e:
        print(f"Gagal klik Next final: {e}")
        return False

    # Verifikasi proses selesai
    time.sleep(2)
    if d(className="android.widget.MultiAutoCompleteTextView").exists:
        print("Masih di halaman age input!")
        save_xml_to_file(d, "process_not_completed")
        return False

    print("Proses pengisian birthday selesai!")
    return True
    
def get_utc_timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def save_registration_result(result_data):
    """Menyimpan hasil registrasi dan secara otomatis membaca cookie dari file."""
    timestamp = get_utc_timestamp().replace(':', '-').replace(' ', '_')
    filename = f"hasil_registrasi_{timestamp}.txt"
    cookie_file_path = "captured_cookies.txt"

    print("\n--- MENCARI COOKIE YANG DITANGKAP OLEH MITMPROXY ---")
    # Beri jeda beberapa detik untuk memastikan mitmproxy selesai menulis file
    time.sleep(5) 

    cookie_string = ""
    if os.path.exists(cookie_file_path):
        with open(cookie_file_path, "r", encoding="utf-8") as f:
            cookie_string = f.read()
        os.remove(cookie_file_path) # Hapus file agar siap untuk registrasi berikutnya
        print("✅ Cookie ditemukan dan berhasil dibaca.")
    else:
        print("⚠️ File cookie tidak ditemukan. Registrasi mungkin gagal atau cookie tidak tertangkap.")

    # Simpan semua data gabungan ke file
    with open(filename, "w", encoding="utf-8") as f:
        for key, value in result_data.items():
            f.write(f"{key}: {value}\n")

        f.write("\n=== COOKIES ===\n")
        if cookie_string:
            f.write(cookie_string)
        else:
            f.write("(Otomatisasi gagal menangkap cookie)")

    print(f"✅ Hasil registrasi lengkap telah disimpan ke: {filename}")

def check_instagram_lite_installed(d):
    return d.app_info("com.instagram.lite")

def uninstall_instagram_lite(d):
    print("Menguninstall Instagram Lite...")
    d.app_uninstall("com.instagram.lite")
    print("Uninstall selesai.")

def install_instagram_lite(d):
    if not os.path.exists(APK_PATH):
        print(f"File APK tidak ditemukan di: {APK_PATH}"); return False
    print(f"Menginstall Instagram Lite...")
    d.app_install(APK_PATH)
    time.sleep(15) 
    if not d.app_info("com.instagram.lite"):
        print("Verifikasi instalasi gagal."); return False
    print("Instalasi berhasil.")
    return True

# --- FUNGSI INTI PENDAFTARAN ---
def register_instagram_lite(d, fullname, password):
    activation_id, full_number = request_phone_number(API_KEY, ID_NEGARA, service='ig')
    if not activation_id or not full_number:
        print(f"Nomor telepon untuk negara ID {ID_NEGARA} tidak tersedia atau gagal divalidasi.")
        return False
    
    phone_code = get_phone_code(ID_NEGARA)
    if not phone_code:
        print(f"Kode telepon untuk negara ID {ID_NEGARA} tidak ditemukan.")
        return False
    
    local_number = strip_country_code(full_number, phone_code)
    print(f"Nomor Telepon Didapat: +{phone_code}{local_number} (Lokal: {local_number})")
    xpath_create = '//android.widget.FrameLayout[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout/android.view.ViewGroup[2]/android.view.ViewGroup[2]'
    if d.xpath(xpath_create).wait(timeout=20): # Menggunakan wait
        d.xpath(xpath_create).click()
        time.sleep(5)
    else:
        print("Tombol 'Create new account' tidak ditemukan!")
        return False

    # Klik field code negara
    d.xpath('//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[2]').click()
    time.sleep(2)
    # Klik search, isi kode negara
    if d.xpath('//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[1]/android.view.ViewGroup[1]/android.view.View[1]').wait(timeout=5):
        d.xpath('//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[1]/android.view.ViewGroup[1]/android.view.View[1]').click()
    search_field = d(className="android.widget.MultiAutoCompleteTextView")
    search_field.set_text(phone_code)
    time.sleep(2)
    # Pilih negara pertama
    d.xpath('//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[1]').click_exists(timeout=5)
    time.sleep(1)

    # Isi nomor hp lokal
    phone_field = d(className="android.widget.MultiAutoCompleteTextView")
    phone_field.set_text(local_number)
    time.sleep(1)

    # Klik Next
    d.xpath('//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[3]').click_exists(timeout=5)
    print("Nomor dan negara berhasil diinput, menunggu halaman verifikasi kode...")

    # Menunggu halaman verifikasi kode muncul
    print("Menunggu halaman verifikasi kode muncul...")
    
    otp_field_selector = d(className="android.widget.MultiAutoCompleteTextView", textContains="_")
    if otp_field_selector.wait(timeout=30):
        print("Halaman verifikasi terdeteksi (berdasarkan field input).")
        print("Meminta kode OTP dari API...")
        
        otp = get_sms_code(API_KEY, activation_id)
        if not otp:
            print("Tidak menerima kode OTP dari API. Proses registrasi gagal.")
            return False
        # Mengisi kode ke field yang sama yang sudah kita temukan
        # Kita panggil selectornya lagi untuk memastikan elemennya fresh
        d(className="android.widget.MultiAutoCompleteTextView", textContains="_").set_text(otp)
        print(f"Kode OTP '{otp}' berhasil diinput.")
        time.sleep(1)
    else:
        print("Gagal mendeteksi halaman verifikasi kode dalam 30 detik.")
        return False

    # Klik tombol Next setelah memasukkan OTP
    if d.xpath('//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[3]').click_exists(timeout=10):
        print("Tombol Next (setelah OTP) diklik.")
    else:
        d.click(500, 400) 
        print("Tombol Next (setelah OTP) diklik via koordinat.")

    time.sleep(3)
    
    print("Mencari dan mengisi field nama lengkap & password...")
    for _ in range(10):
        mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
        if mac_fields.exists and mac_fields.count >= 2:
            name_field = mac_fields[0]
            pass_field = mac_fields[1]
            name_field.click()
            time.sleep(0.5)
            name_field.clear_text()
            name_field.set_text(fullname)
            time.sleep(1)
            print(f"Field nama lengkap diisi dengan '{fullname}'.")
            
            pass_field.click()
            time.sleep(0.5)
            pass_field.clear_text()
            pass_field.set_text(password)
            time.sleep(1)
            print("Field password diisi.")
            break
        print("Field nama lengkap/password belum muncul, menunggu...")
        time.sleep(1)
    else:
        print("Field nama lengkap/password tidak ditemukan! Cek UI.")
        return False

    print("Klik Next untuk melanjutkan registrasi...")
    if d(text="Next").exists:
        d(text="Next").click()
        print("Tombol Next diklik berdasarkan text.")
    elif d(text="Berikutnya").exists:
        d(text="Berikutnya").click()
        print("Tombol Berikutnya diklik.")
    else:
        d.click(450, 513)
        print("Tombol Next diklik berdasarkan koordinat.")
    time.sleep(3)

    print("Masuk ke halaman birthday, mengisi tanggal lahir...")
    if not set_birthday(d):
        print("Gagal mengatur tanggal lahir. Proses dihentikan.")
        return False
    
    print("halaman 'your account is almost ready'...")
    time.sleep(2)
    
    xpathnext = '//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[6]'
    if d.xpath(xpathnext).wait(timeout=15):      
        d.xpath(xpathnext).click()
        print("Tombol next pada halaman 'almost ready' berhasil diklik via xpath.")
        time.sleep(2)
    elif d(text="Next").wait(timeout=5):
        d(text="Next").click()
        print("Tombol Next diklik via text.")
        time.sleep(2)
    else:
        print("Tombol Next pada halaman 'almost ready' tidak ditemukan!") 
        
    print('masuk ke halaman sync contact')
    time.sleep(5)
    xpath_skip_contacts = '//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[3]/android.view.View[1]'
    if d.xpath(xpath_skip_contacts).wait(timeout=15):
        d.xpath(xpath_skip_contacts).click()
        print("Tombol Skip pada halaman sync kontak berhasil diklik via xpath.")
        time.sleep(2)
    elif d(text="Skip").wait(timeout=5):
        d(text="Skip").click()
        print("Tombol Skip diklik via text.")
        time.sleep(2)
    else:
        print("Tombol Skip pada halaman sync kontak tidak ditemukan!")
        
    print("Mencoba melewati halaman profil poto")
    xpathskips = '//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[3]/android.view.View[1]'
    if d.xpath(xpathskips).wait(timeout=10):
        d.xpath(xpathskips).click()
        print("Tombol Skip pada halaman add poto berhasil diklik via xpath.")
        time.sleep(2)
    else:
        print("Halaman 'add poto' tidak ditemukan atau sudah dilewati.")
        
    print("halaman follow 5 orangs")
    xpathnextf = '//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[1]'
    if d.xpath(xpathnextf).wait(timeout=10):
        d.xpath(xpathnextf).click()
        print("Tombol next (follow) berhasil di klik")
        time.sleep(5)
    else:
        print("Halaman 'follow' tidak ditemukan atau sudah dilewati.")
        
    print("\n✨ REGISTRASI BERHASIL ✨")
    print("Masuk Ke halaman HOME")
    print("\nCollecting registration results...")

    registration_result = {
        'status': 'success',
        'username': fullname,
        'password': password,
        'phone_number': f"+{phone_code}{local_number}", 
        'email': 'N/A', 
        'registration_time': get_utc_timestamp(),
        'system_user': os.getlogin()
    }

# Panggil fungsi yang sudah dimodifikasi
    save_registration_result(registration_result) 

# Hapus sisa kode yang mencoba print cookie secara manual dari variabel

    return registration_result
# --- FUNGSI UTAMA ---
def main():
    jumlah_akun_didaftar = 3
    start_ldplayer_and_connect_adb()

    for i in range(jumlah_akun_didaftar):
        print(f"\n===== MEMULAI PENDAFTARAN AKUN KE-{i + 1} DARI {jumlah_akun_didaftar} =====")
        d = None
        try:
            check_current_ip()
            
            d = connect_device()
            print("Koneksi diasumsikan sudah melalui proxy di PC.")
            time.sleep(2)

            # --- LOGIKA BARU YANG LEBIH ANDAL ---
            print("Memastikan Instagram Lite dalam keadaan fresh install...")
            
            # 1. Selalu coba uninstall terlebih dahulu untuk membersihkan.
            #    Perintah ini tidak akan error jika aplikasi tidak ada.
            d.app_uninstall("com.instagram.lite")
            print("-> Proses uninstall (jika ada) selesai.")
            time.sleep(3) # Beri jeda sejenak

            # 2. Selalu jalankan proses instalasi.
            if install_instagram_lite(d):
                print("-> Instalasi Instagram Lite berhasil.")
                time.sleep(5) # Beri jeda untuk memastikan aplikasi siap
                handle_permission_popup(d)
                # Jika instalasi berhasil, lanjutkan pendaftaran
                print("-> Instalasi berhasil, melanjutkan ke pendaftaran.")
                new_fullname = generate_random_fullname()
                new_password = generate_random_password()
                register_instagram_lite(d, new_fullname, new_password)
            else:
                # Jika instalasi gagal, hentikan siklus ini dan lanjut ke akun berikutnya
                print("❌ Gagal menginstall Instagram Lite, siklus ini dibatalkan.")
                continue

        except Exception as e:
            print(f"Terjadi error besar pada pendaftaran akun ke-{i + 1}: {e}")
            if d:
                d.screenshot(f"error_utama_{i+1}.png")
                print(f"Screenshot error disimpan sebagai error_utama_{i+1}.png")
        
        finally:
            print("Siklus pendaftaran selesai. Jeda 15 detik...")
            time.sleep(15)

    print("\n===== SEMUA PROSES PENDAFTARAN SELESAI =====")

# --- BLOK EKSEKUSI UTAMA ---
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nTerjadi error yang tidak tertangani di level utama: {e}")
