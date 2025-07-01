import os, string
import subprocess
import time
from datetime import datetime, timezone
import uiautomator2 as u2
import uuid
import random
from gmail_api_utils import get_verification_code_from_email_gmail_api

# KONFIGURASI PATH DAN DEVICE UNTUK LDPLAYER
LDPLAYER_EXE_PATH = r"C:\LDPlayer\LDPlayer9\dnplayer.exe"
ADB_PATH = r"C:\LDPlayer\LDPlayer9\adb.exe"
LDPLAYER_DEVICE = "emulator-5554"

# Data akun yang ingin diregistrasikan (ganti sesuai kebutuhan)
EMAIL = "otomatisregis@gmail.com"

# Konfigurasi IMAP untuk Gmail
#IMAP_SERVER = "imap.gmail.com"
#IMAP_PORT = 993

def generate_random_fullname(length=10):
    # Membuat username random, misal: "user123abc"
    chars = string.ascii_lowercase + string.digits
    return 'soap' + ''.join(random.choices(chars, k=length))

def generate_random_password(length=12):
    # Kombinasi huruf besar, kecil, angka, dan simbol
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=length))

FULLNAME = generate_random_fullname()
PASSWORD = generate_random_password()

def inspect_ui_elements(d, filter_texts=None):
    print("\n======= UI Elements Inspector (Filtered) =======\n")
    try:
        dump = d.dump_hierarchy(compressed=False, pretty=True)
        elements = d.xpath('//*').all()
        total_elements = len(elements)
        print(f"Total elements found: {total_elements}")

        found_matching = False
        for element in elements:
            text = element.attrib.get('text')
            resource_id = element.attrib.get('resource-id')
            class_name = element.attrib.get('class')
            bounds = element.attrib.get('bounds')
            clickable = element.attrib.get('clickable')

            display_element = False
            if filter_texts:
                for f_text in filter_texts:
                    if (text and f_text.lower() in text.lower()) or \
                       (resource_id and f_text.lower() in resource_id.lower()) or \
                       (class_name and f_text.lower() in class_name.lower()):
                        display_element = True
                        found_matching = True
                        break
            else:
                display_element = True # Display all if no filter

            if display_element:
                print(f"  Text: {text}")
                print(f"  Resource ID: {resource_id}")
                print(f"  Class Name: {class_name}")
                print(f"  Bounds: {bounds}")
                print(f"  Clickable: {clickable}")
                print("-" * 20)

        if filter_texts and not found_matching:
            print("No matching elements found with the provided filters.")
        print("\n=================================================\n")
    except Exception as e:
        print(f"Error inspecting UI elements: {e}")
        
def start_ldplayer_and_connect_adb():
    print("Menjalankan emulator LDPlayer...")
    subprocess.Popen([LDPLAYER_EXE_PATH])
    max_wait = 180  # detik
    wait_time = 0
    offline_count = 0
    while wait_time < max_wait:
        out = subprocess.getoutput(f'"{ADB_PATH}" devices')
        print("ADB devices output:", out)
        lines = out.splitlines()
        found_online = False
        for line in lines:
            if "device" in line and "offline" not in line and "List of devices" not in line:
                print(f"Emulator siap, adb sudah terhubung sebagai: {line.strip()}")
                global LDPLAYER_DEVICE
                LDPLAYER_DEVICE = line.split()[0]
                return
            if "offline" in line:
                offline_count += 1
        if offline_count > 5:
            print("Device selalu offline, kemungkinan ada masalah dengan ADB/LDPlayer.")
            print("Cek apakah LDPlayer sudah benar-benar running, atau coba restart ADB dan emulator.")
            raise RuntimeError("Device ADB selalu offline. Proses dihentikan.")
        print("ADB belum terhubung ke emulator, mencoba connect ke port umum LDPlayer...")
        for port in [5554, 5555, 5556, 62001]:
            os.system(f'"{ADB_PATH}" connect 127.0.0.1:{port}')
        time.sleep(3)
        wait_time += 3
    raise RuntimeError("Gagal mendapatkan koneksi ADB ke emulator! Pastikan LDPlayer sudah running dan Android siap.")

def unlock_screen():
    print("Membuka kunci layar (jika terkunci)...")
    os.system(f'"{ADB_PATH}" -s {LDPLAYER_DEVICE} shell input keyevent 224')
    os.system(f'"{ADB_PATH}" -s {LDPLAYER_DEVICE} shell input keyevent 82')

def wait_and_click(d, text=None, resourceId=None, bounds=None, timeout=20):
    for _ in range(timeout):
        if text and d(text=text).exists:
            d(text=text).click()
            return True
        if resourceId and d(resourceId=resourceId).exists:
            d(resourceId=resourceId).click()
            return True
        if bounds and d(className="android.view.ViewGroup", clickable=True, bounds=bounds).exists:
            d(className="android.view.ViewGroup", clickable=True, bounds=bounds).click()
            return True
        time.sleep(1)
    print(f"Element {text or resourceId or bounds} not found.")
    return False

def wait_for(d, text=None, resourceId=None, bounds=None, timeout=20):
    for _ in range(timeout):
        if text and d(text=text).exists:
            return True
        if resourceId and d(resourceId=resourceId).exists:
            return True
        if bounds and d(className="android.view.ViewGroup", clickable=True, bounds=bounds).exists:
            return True
        time.sleep(1)
    return False

def handle_permission_popup(d, timeout=10):
    """
    Menangani pop-up perizinan Instagram Lite secara otomatis.
    Akan mengklik tombol ALLOW/IZINKAN untuk semua jenis perizinan.
    """
    print("Memulai pengecekan pop-up perizinan...")
    
    permission_handled = False
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Cek berbagai variasi tombol Allow/Izinkan
        permission_buttons = [
            "ALLOW",
            "Allow", 
            "IZINKAN",
            "Izinkan",
            "OK",
            "WHILE USING THE APP",
            "While using the app"
        ]
        
        for button_text in permission_buttons:
            if d(text=button_text).exists:
                print(f"Pop-up perizinan terdeteksi dengan tombol '{button_text}', mengklik...")
                d(text=button_text).click()
                time.sleep(1)
                permission_handled = True
                print(f"Tombol '{button_text}' berhasil diklik.")
                break
        
        if permission_handled:
            break
            
        # Cek pop-up berdasarkan resource ID jika ada
        permission_resource_ids = [
            "com.android.permissioncontroller:id/permission_allow_button",
            "android:id/button1",
            "com.android.packageinstaller:id/permission_allow_button"
        ]
        
        for resource_id in permission_resource_ids:
            if d(resourceId=resource_id).exists:
                print(f"Pop-up perizinan terdeteksi dengan resource ID '{resource_id}', mengklik...")
                d(resourceId=resource_id).click()
                time.sleep(1)
                permission_handled = True
                print(f"Resource ID '{resource_id}' berhasil diklik.")
                break
        
        if permission_handled:
            break
            
        # Cek apakah ada dialog dengan keyword "Instagram Lite" dan "contacts"
        if (d(textContains="Instagram Lite").exists and 
            (d(textContains="contacts").exists or d(textContains="kontak").exists)):
            print("Pop-up perizinan Instagram Lite untuk akses kontak terdeteksi...")
            
            # Cari tombol di bagian kanan bawah dialog (biasanya ALLOW)
            buttons = d(className="android.widget.Button")
            if buttons.exists:
                for i in range(buttons.count):
                    try:
                        button = buttons[i]
                        button_text = button.info.get('text', '')
                        bounds = button.info.get('bounds', {})
                        
                        # Tombol ALLOW biasanya di posisi kanan
                        if bounds and bounds.get('right', 0) > 600:  # Asumsi layar > 600px
                            print(f"Mengklik tombol kanan (kemungkinan ALLOW): '{button_text}'")
                            button.click()
                            time.sleep(1)
                            permission_handled = True
                            break
                    except Exception as e:
                        print(f"Error saat cek button {i}: {e}")
                        continue
        
        if permission_handled:
            break
            
        time.sleep(0.5)  # Mengurangi waktu tunggu antara pengecekan
    
    if permission_handled:
        print("Pop-up perizinan berhasil ditangani.")
    else:
        print("Tidak ada pop-up perizinan yang terdeteksi dalam waktu yang ditentukan.")
    
    return permission_handled

def manual_input_verification_code():
    print("\n" + "="*50)
    print("PERHATIAN: Tidak dapat mengambil kode verifikasi otomatis")
    print("Silakan cek email Anda dan masukkan kode verifikasi secara manual")
    print("="*50)
    while True:
        code = input("Masukkan kode verifikasi (6 digit): ").strip()
        if len(code) == 6 and code.isdigit():
            return code
        else:
            print("Kode harus 6 digit angka. Silakan coba lagi.")

def handle_email_verification(d, max_attempts=3, kode_start_time=None):
    print("Mendeteksi halaman verifikasi email...")
    verification_detected = False
    
    # Set start time jika belum ada
    if kode_start_time is None:
        kode_start_time = time.time()
        print(f"Set kode_start_time ke: {kode_start_time}")
    
    # Deteksi halaman verifikasi dengan timeout lebih pendek
    for attempt in range(15):  # Kurangi timeout menjadi 30 detik
        print(f"Percobaan {attempt + 1}: Mencari halaman verifikasi...")
        indicators = [
            d(textContains="confirmation").exists,
            d(textContains="verification").exists,
            d(textContains="code").exists,
            d(textContains="confirm").exists,
            d(textContains="Enter").exists,
            d(textContains="6-digit").exists,
            d(textContains="digit").exists,
            d(className="android.widget.EditText").exists,
            d(resourceId="com.instagram.lite:id/confirmation_code").exists,
            d(className="android.widget.MultiAutoCompleteTextView").exists,
        ]
        if any(indicators):
            verification_detected = True
            print("Halaman verifikasi email terdeteksi!")
            break
        time.sleep(2)
        
    if not verification_detected:
        print("Halaman verifikasi tidak terdeteksi setelah 30 detik")
        return False

    exclude_codes = []
    for attempt in range(max_attempts):
        print(f"Percobaan verifikasi kode ke-{attempt+1}...")
        
        # Tambahkan jeda sebelum mencoba mendapatkan kode
        if attempt > 0:
            print("Menunggu 10 detik sebelum mencoba lagi...")
            time.sleep(10)
        
        # Ambil kode verifikasi dengan timeout yang lebih pendek
        print("Mencoba mengambil kode verifikasi dari email...")
        verification_code = get_verification_code_from_email_gmail_api(
            timeout=60,  # 1 menit timeout
            exclude_codes=exclude_codes,
            start_time=kode_start_time
        )
        
        if verification_code:
            print(f"Kode verifikasi ditemukan: {verification_code}")
        else:
            print("Tidak dapat mengambil kode otomatis, mencoba input manual...")
            verification_code = manual_input_verification_code()
            
        if not verification_code:
            print("Tidak ada kode verifikasi yang tersedia!")
            continue
            
        exclude_codes.append(verification_code)
        print(f"Memasukkan kode verifikasi: {verification_code}")

        # Isi field kode
        success = False
        
        # Coba resource ID yang paling umum dulu
        primary_resource_ids = [
            "com.instagram.lite:id/confirmation_code",
            "com.instagram.lite:id/code_text",
        ]
        
        for resource_id in primary_resource_ids:
            if d(resourceId=resource_id).exists:
                try:
                    code_field = d(resourceId=resource_id)
                    code_field.click()
                    time.sleep(1)
                    code_field.clear_text()
                    time.sleep(0.5)
                    code_field.set_text(verification_code)
                    time.sleep(2)
                    success = True
                    break
                except Exception as e:
                    print(f"Error pada resource ID {resource_id}: {e}")
                    continue

        if not success:
            # Coba EditText
            edit_texts = d(className="android.widget.EditText")
            if edit_texts.exists:
                for i in range(min(edit_texts.count, 3)):
                    try:
                        field = edit_texts[i]
                        field.click()
                        time.sleep(0.5)
                        field.clear_text()
                        time.sleep(0.5)
                        field.set_text(verification_code)
                        time.sleep(1)
                        success = True
                        break
                    except Exception as e:
                        print(f"Error pada EditText {i}: {e}")
                        continue

        if not success:
            # Fallback ke koordinat
            x, y = 450, 180
            d.click(x, y)
            time.sleep(1)
            d.send_keys(verification_code)
            time.sleep(1)
            success = True

        if success:
            # Klik tombol Next
            if d(text="Next").exists:
                d(text="Next").click()
            elif d(textContains="Next").exists:
                d(textContains="Next").click()
            else:
                d.click(450, 400)
            
            print("Menunggu response setelah input kode...")
            time.sleep(5)

            # Cek hasil verifikasi
            if d(textContains="That code isn't valid").exists or d(textContains="incorrect").exists:
                print("Kode tidak valid, mencoba kode baru...")
                continue
            else:
                # Tunggu dan cek apakah masih di halaman verifikasi
                time.sleep(3)
                if not any([
                    d(textContains="confirmation").exists,
                    d(textContains="verification").exists,
                    d(textContains="code").exists
                ]):
                    print("Verifikasi berhasil!")
                    return True
                else:
                    print("Masih di halaman verifikasi, mencoba kode baru...")
                    continue

    print("Gagal verifikasi setelah beberapa percobaan.")
    return False

def handle_existing_account_popup(d, timeout=15):
    """
    Menangani pop-up dari Instagram Lite ketika email sudah terdaftar di akun lain.
    WAJIB klik tombol 'Create new account' via XPath sebelum lanjut.
    """
    print("Memeriksa pop-up email sudah terdaftar di Instagram Lite...")

    xpath_create_new_account = (
        "//android.widget.FrameLayout[@resource-id=\"com.instagram.lite:id/main_layout\"]"
        "/android.widget.FrameLayout/android.view.ViewGroup[3]/android.view.ViewGroup"
        "/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]"
    )

    start_time = time.time()
    while time.time() - start_time < timeout:
        # Cek apakah popup muncul
        if (d(text="This email is on another account").exists or
            d(textContains="email is on another account").exists or
            d.xpath(xpath_create_new_account).exists):
            print("Popup 'email is on another account' Terdeteksi")
            # Klik tombol "Create new account" via XPath AKURAT
            if d.xpath(xpath_create_new_account).exists:
                print("Klik tombol 'Create new account' (XPath)")
                d.xpath(xpath_create_new_account).click()
                time.sleep(2)
                # Tunggu popup benar-benar hilang sebelum lanjut
                for _ in range(10):
                    if not d.xpath(xpath_create_new_account).exists:
                        print("Popup sudah hilang.")
                        return True
                    time.sleep(0.5)
                print("Popup belum hilang setelah klik. Coba lagi...")
            else:
                print("XPath 'Create new account' tidak ditemukan. Inspect UI...")
                inspect_ui_elements(d)
        time.sleep(0.5)

    print("Pop-up email sudah terdaftar tidak terdeteksi atau gagal klik.")
    return False

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
    xpath_next = '//android.widget.FrameLayout[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout/android.view.ViewGroup[3]/android.view.ViewGroup[3]'
    
    if d.xpath(xpath_next).exists:
        d.xpath(xpath_next).click()
        print("Tombol Next berhasil diklik")
        time.sleep(2)
    else:
        print("Gagal menemukan tombol Next!")
        return False

    # --- LANGKAH 2: Menangani popup 'Enter your real birthday' ---
    print("\nLangkah 2: Menangani popup birthday...")
    #save_xml_to_file(d, "before_popup")
    time.sleep(2)

    # Klik OK di popup
    try:
        d.click(450, 800)  # Koordinat tengah
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
    #save_xml_to_file(d, "after_popup")
    
    # Coba klik menggunakan koordinat yang tepat dari XML
    try:
        d.click(450, 1495)  # Titik tengah dari bounds="[354,1481][546,1510]"
        print("Enter age instead diklik via koordinat yang tepat")
        time.sleep(3)
    except Exception as e:
        print(f"Gagal klik Enter age instead via koordinat: {e}")
        return False

    # Verifikasi halaman Enter your age muncul
    #save_xml_to_file(d, "enter_age_verification")
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
        d.click(450, 418)  # Titik tengah dari bounds Next button
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

def save_registration_result(result_data, cookies=None):
    timestamp = get_utc_timestamp()
    filename = f"registration_result_{timestamp.replace(':', '_').replace(' ', '_')}.txt"
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=== INSTAGRAM LITE REGISTRATION RESULT ===\n")
            f.write(f"Registration Time (UTC): {timestamp}\n")
            f.write(f"System User: {os.getlogin()}\n")
            f.write("\n=== ACCOUNT DETAILS ===\n")
            f.write(f"Status: {result_data.get('status', 'N/A')}\n")
            f.write(f"Username: {result_data.get('username', 'N/A')}\n")
            f.write(f"Password: {result_data.get('password', 'N/A')}\n")
            f.write(f"Email: {result_data.get('email', 'N/A')}\n")
            
            if cookies:
                f.write("\n=== COOKIES ===\n")
                f.write(cookies)
                
            f.write("\n\n=== ADDITIONAL INFO ===\n")
            f.write(f"Device: {LDPLAYER_DEVICE}\n")
            f.write(f"Instagram Lite Package: com.instagram.lite\n")
            
        print(f"\nRegistration result saved to: {filename}")
        return True
    except Exception as e:
        print(f"Error saving registration result: {e}")
        return False

def check_instagram_lite_installed():
    print("Mengecek apakah Instagram Lite sudah terinstall...")
    try:
        result = subprocess.getoutput(f'"{ADB_PATH}" -s {LDPLAYER_DEVICE} shell pm list packages com.instagram.lite')
        print(f"Hasil ADB: {result}")
        if "com.instagram.lite" in result:
            print("Instagram Lite sudah terinstall.")
            return True
    except Exception as e:
        print(f"Error saat mengecek aplikasi terinstall: {e}")
    print("Instagram Lite belum terinstall.")
    return False

def install_instagram_lite():
    print("Menghubungkan ke emulator dengan uiautomator2...")
    d = u2.connect(LDPLAYER_DEVICE)
    print("Membuka Google Play Store...")
    d.app_start("com.android.vending")
    time.sleep(4)
    print("Klik search bar di bagian atas (LDPlayer)...")
    d.click(350, 60)
    time.sleep(2)
    d.send_keys("Instagram Lite")
    time.sleep(3)
    d.press("enter")
    time.sleep(3)
    print("Klik tombol Install di panel kanan (detail aplikasi, via XPath)...")
    xpath_install = '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View[2]/android.view.View/android.view.View[1]/android.view.View[5]/android.widget.Button[2]'
    if d.xpath(xpath_install).exists:
        d.xpath(xpath_install).click()
        print("Tombol Install (detail aplikasi) berhasil diklik via XPath.")
    elif d(text="Install").exists:
        d(text="Install").click()
        print("Tombol Install diklik via text (fallback).")
    else:
        print("Tombol Install tidak ditemukan! Gagal install Instagram Lite.")
        return False
    
    print("Menunggu proses install selesai (tombol Buka muncul)...")
    for _ in range(120):
        # Tambahkan pengecekan tombol Open dengan XPath yang diberikan
        xpath_open = '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View[2]/android.view.View/android.view.View[1]/android.view.View[5]/android.widget.Button'
        if d.xpath(xpath_open).exists:
            print("Tombol Open ditemukan via XPath, mengklik...")
            d.xpath(xpath_open).click()
            time.sleep(5)
            # Handle permission popup setelah membuka aplikasi
            handle_permission_popup(d)
            return True
        elif d(text="Open").exists:
            print("Tombol Open ditemukan via text, mengklik...")
            d(text="Open").click()
            time.sleep(5)
            # Handle permission popup setelah membuka aplikasi
            handle_permission_popup(d)
            return True
        elif d(text="Buka").exists:
            print("Tombol Buka ditemukan, mengklik...")
            d(text="Buka").click()
            time.sleep(5)
            # Handle permission popup setelah membuka aplikasi
            handle_permission_popup(d)
            return True
        time.sleep(4)
    print("Timeout: Gagal mendeteksi bahwa Instagram Lite sudah terinstall.")
    return False

def register_instagram_lite(email, fullname, password):
    def save_xml_to_file(d, prefix):
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.xml"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(d.dump_hierarchy())
            print(f"Saved XML inspection to {filename}")
        except Exception as e:
            print(f"Gagal menyimpan XML: {e}")
    d = u2.connect(LDPLAYER_DEVICE)
    print("Membuka aplikasi Instagram Lite...")
    d.app_start("com.instagram.lite")
    time.sleep(10)
    handle_permission_popup(d, timeout=10)

    print("Inspect elemen setelah aplikasi dibuka:")
    inspect_ui_elements(d, filter_texts=["create", "account", "button"])

    print("Klik tombol 'Create new account'")
    xpath_create_new_account = '//android.widget.FrameLayout[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout/android.view.ViewGroup[2]/android.view.ViewGroup[2]'
    if d.xpath(xpath_create_new_account).exists:
        d.xpath(xpath_create_new_account).click()
        print("Tombol 'Create new account' berhasil diklik via XPath.")
        time.sleep(5)
    else:
        print("Tombol 'Create new account' tidak ditemukan!")
        inspect_ui_elements(d, filter_texts=["create", "account", "button"])
        return

    print("Klik tombol 'Sign up with email'")
    xpath_signup_email = '//android.widget.FrameLayout[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout/android.view.ViewGroup[3]/android.view.ViewGroup[3]'
    if d.xpath(xpath_signup_email).exists:
        d.xpath(xpath_signup_email).click()
        print("Tombol 'Sign up with email' berhasil diklik via XPath.")
        time.sleep(5)
    else:
        found = False
        for _ in range(5):
            if d(text="Sign up with email").exists:
                d(text="Sign up with email").click()
                print("Tombol 'Sign up with email' berhasil diklik via text.")
                found = True
                time.sleep(5)
                break
            elif d(textContains="email").exists:
                d(textContains="email").click()
                print("Tombol 'Sign up with email' berhasil diklik via textContains.")
                found = True
                time.sleep(5)
                break
            time.sleep(1)
        if not found:
            print("Tombol 'Sign up with email' tidak ditemukan!")
            inspect_ui_elements(d, filter_texts=["email"])
            return

    print("Mengisi field email...")
    for _ in range(10):
        email_field = d(className="android.widget.MultiAutoCompleteTextView")
        if email_field.exists:
            email_field.clear_text()
            time.sleep(0.5)
            email_field.set_text(email)
            time.sleep(2)
            print(f"Email '{email}' berhasil diisi")
            break
        time.sleep(1)
    else:
        print("Field email tidak ditemukan!")
        inspect_ui_elements(d, filter_texts=["email"])
        return
    print("Mencari tombol Next...")
    next_clicked = False
    if d(text="Next").exists:
        d(text="Next").click()
        next_clicked = True
    elif d(textContains="Next").exists:
        d(textContains="Next").click()
        next_clicked = True
    elif d(resourceId="com.instagram.lite:id/next_button").exists:
        d(resourceId="com.instagram.lite:id/next_button").click()
        next_clicked = True
    else:
        print("Mencoba klik tombol Next dengan koordinat alternatif...")
        d.click(450, 420)
        next_clicked = True
    if next_clicked:
        print("Tombol Next berhasil diklik, menunggu halaman berikutnya...")
        print("Menunggu 15 detik untuk email verifikasi masuk...")
        time.sleep(15)
    # WAJIB: Tunggu dan handle popup jika muncul
        handled = handle_existing_account_popup(d, timeout=10)
        if handled:
            print("Popup existing account berhasil dihandle, lanjutkan registrasi.")
            time.sleep(1)
        else:
            print("Tidak ada pop-up email terdaftar yang muncul, melanjutkan...")
    else:
        print("Gagal menemukan tombol Next!")
        return

    print("Cek apakah langsung masuk ke halaman verifikasi kode...")
    for _ in range(10):
        mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
        if mac_fields.exists and "_" in mac_fields[0].info.get("text", ""):
            print("Halaman verifikasi kode terdeteksi, mengeksekusi handle_email_verification ...")
            verif_ok = handle_email_verification(d)
            print("Registrasi: handle_email_verification selesai. Melanjutkan isi nama lengkap & password.")
            for _ in range(15):
                mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
                if not (mac_fields.exists and "_" in mac_fields[0].info.get("text", "")):
                    print("Field kode sudah hilang, lanjut ke pengisian nama lengkap.")
                    break
                print("Masih di halaman verifikasi kode, menunggu...")
                time.sleep(1)
            break
        time.sleep(1)

    print("Mencari dan mengisi field nama lengkap & password...")
    for _ in range(10):
        mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
        if mac_fields.exists and mac_fields.count >= 2:
            name_field = mac_fields[0]
            pass_field = mac_fields[1]
            name_field.click()
            name_field.clear_text()
            name_field.set_text(fullname)
            time.sleep(1)
            print(f"Field nama lengkap diisi dengan '{fullname}'.")
            pass_field.click()
            pass_field.clear_text()
            pass_field.set_text(password)
            time.sleep(1)
            print("Field password diisi.")
            break
        print("Field nama lengkap/password belum muncul, menunggu...")
        time.sleep(1)
    else:
        print("Field nama lengkap/password tidak ditemukan! Cek UI.")
        return

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
    set_birthday(d)
    
    print("\nMenangani halaman 'your account is almost ready'...")
    time.sleep(3)

    try:
        print("Mencoba klik tombol Next (area atas)...")
        # Target the "Next" button using text match with clickable check
        if d(text="Next", clickable=True).exists:
            d(text="Next", clickable=True).click()
            print("Tombol Next berhasil diklik berdasarkan text dan clickable.")
        else:
            # Fallback to coordinates near the center of the "Next" button (adjust based on screenshot)
            d.click(450, 1463)  # Adjusted to target the blue "Next" button
            time.sleep(2)
            if "your account is almost ready" in d.dump_hierarchy().lower():
                print("Masih di halaman yang sama, mencoba posisi alternatif...")
                click_positions = [
                    (350, 1463),  # Sisi kiri atas
                    (550, 1463),  # Sisi kanan atas
                    (450, 1480),  # Sedikit lebih bawah untuk memastikan tombol
                ]
                for x, y in click_positions:
                    print(f"Mencoba klik di koordinat ({x}, {y})")
                    d.click(x, y)
                    time.sleep(2)
                    if "your account is almost ready" not in d.dump_hierarchy().lower():
                        print(f"Berhasil! Klik di ({x}, {y}) berhasil")
                        break
        # Final verification
        if "your account is almost ready" not in d.dump_hierarchy().lower():
            print("Berhasil melanjutkan dari halaman 'your account is almost ready'")
        else:
            print("Gagal melanjutkan, masih di halaman yang sama")
            save_xml_to_file(d, "still_on_account_ready")

    except Exception as e:
        print(f"Error saat mencoba mengklik tombol Next: {e}")
        save_xml_to_file(d, "error_clicking_next")
    
    save_xml_to_file(d, "halaman selanjutnya")
    xpath_skip_contacts = '//android.widget.FrameLayout[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout/android.view.ViewGroup[3]/android.view.ViewGroup[3]'
    for _ in range(10):
        if d.xpath(xpath_skip_contacts).exists:
            d.xpath(xpath_skip_contacts).click()
            print("Tombol Skip pada halaman sync kontak berhasil diklik via xpath.")
            time.sleep(2)
            break
        elif d(text="Skip").exists:
            d(text="Skip").click()
            print("Tombol Skip diklik via text.")
            time.sleep(2)
            break
        time.sleep(1)
    else:
        print("Tombol Skip pada halaman sync kontak tidak ditemukan!")
    

    print("\n=== REGISTRASI BERHASIL ===")
    # Get registration result
    print("\nCollecting registration results...")
    registration_result = {
        'status': 'success' if next_clicked else 'warning',
        'username': fullname,
        'password': password,
        'email': email,
        'registration_time': get_utc_timestamp(),
        'system_user': os.getlogin()
    }

    # Get cookies
    try:
        cookies = d.shell(['cat', '/data/data/com.instagram.lite/app_webview/Cookies']).output
        print("\nSuccessfully retrieved cookies")
    except Exception as e:
        print(f"Failed to get cookies: {e}")
        cookies = None

    # Save and display results
    save_registration_result(registration_result, cookies)
    
    print("\n=== REGISTRATION COMPLETED ===")
    print(f"Status: {registration_result['status']}")
    print(f"Username: {registration_result['username']}")
    print(f"Password: {registration_result['password']}")
    print(f"Email: {registration_result['email']}")
    print(f"Registration Time (UTC): {registration_result['registration_time']}")
    print(f"System User: {registration_result['system_user']}")
    
    if cookies:
        print("\n=== COOKIES RETRIEVED ===")
        print(cookies)

    return registration_result

def main():
    start_ldplayer_and_connect_adb()
    unlock_screen()
    print("Menunggu 10 detik sebelum memulai automasi...")
    time.sleep(10)
    if check_instagram_lite_installed():
        print("Instagram Lite sudah terinstall, langsung menuju proses registrasi...")
        time.sleep(2)
        register_instagram_lite(EMAIL, FULLNAME, PASSWORD)
    else:
        print("Instagram Lite belum terinstall, memulai proses install...")
        if install_instagram_lite():
            print("Instagram Lite berhasil diinstall, melanjutkan ke proses registrasi...")
            time.sleep(5)
            register_instagram_lite(EMAIL, FULLNAME, PASSWORD)
        else:
            print("Automasi install Instagram Lite gagal, proses dihentikan.")

if __name__ == "__main__":
    try:
        result = main()
        if isinstance(result, dict):
            print("\n=== FINAL RESULTS ===")
            print(f"Registration Status: {result.get('status', 'N/A')}")
            print(f"Username: {result.get('username', 'N/A')}")
            print(f"Password: {result.get('password', 'N/A')}")
            print(f"Email: {result.get('email', 'N/A')}")
            print(f"Registration Time (UTC): {result.get('registration_time', 'N/A')}")
            print(f"System User: {result.get('system_user', 'N/A')}")
    except Exception as e:
        print(f"\nError in main execution: {e}")
