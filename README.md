# Otomatisasi Instalasi & Pembuatan Akun Instagram Lite di LDPlayer

Proyek ini bertujuan untuk mengotomatisasi proses instalasi Instagram Lite dan pembuatan akun secara otomatis di emulator **LDPlayer** menggunakan Python. Terdapat integrasi dengan Gmail API untuk mengambil kode verifikasi saat pendaftaran akun Instagram.

## Fitur Utama

- Instalasi otomatis Instagram Lite APK di emulator LDPlayer melalui Google Play Store.
- Pembuatan akun Instagram secara otomatis, termasuk pengisian email, nama, password, dan tanggal lahir.
- Otomatisasi pengambilan kode verifikasi dari email Gmail menggunakan Gmail API.
- Penanganan otomatis pop-up perizinan aplikasi, birthday, dan situasi email sudah terdaftar.
- Logging dan error handling untuk mempermudah debugging.

## Struktur Folder & File Utama

- `main.py`  
  Script utama yang menjalankan seluruh proses otomasi, termasuk instalasi aplikasi, pembuatan akun, dan interaksi dengan emulator LDPlayer.
- `gmail_api_utils.py`  
  Utilitas untuk mengakses Gmail API dan mengambil kode verifikasi dari email.
- `requirements.txt`  
  Daftar dependencies Python yang diperlukan.
- `compact_log.txt`  
  File log ringkas (jika ada, tergantung implementasi logging).
- **Catatan:** File konfigurasi Google API (`credentials.json` dan `token.json`) harus disiapkan agar fitur Gmail API dapat digunakan.

## Persiapan

1. **Install LDPlayer**  
   Pastikan emulator [LDPlayer](https://ldplayer.net) sudah terpasang di komputer Anda.  
   Lokasi default LDPlayer di script:  
   - `C:\LDPlayer\LDPlayer9\dnplayer.exe`
   - `C:\LDPlayer\LDPlayer9\adb.exe`  
   Jika berbeda, silakan sesuaikan path pada variabel di `main.py`.

2. **Install Python**  
   Gunakan Python 3.x.

3. **Siapkan Gmail API**  
   - Aktifkan Gmail API di Google Cloud Console.
   - Unduh file `credentials.json` dan letakkan di direktori yang sama dengan script.
   - Script akan otomatis menghasilkan `token.json` saat pertama kali dijalankan.

4. **Install dependencies**
    ```
    pip install -r requirements.txt
    ```

## Cara Menjalankan

1. Pastikan LDPlayer sudah berjalan (atau script akan otomatis menjalankannya).
2. Jalankan script utama:
    ```
    python main.py
    ```
3. Ikuti instruksi pada terminal jika ada input manual (misal kode verifikasi email jika tidak terdeteksi otomatis).

## Catatan Penggunaan

- Proyek ini hanya untuk pembelajaran dan riset otomasi. Pastikan mematuhi terms of service Instagram dan LDPlayer.
- Email yang digunakan harus valid dan dapat menerima kode verifikasi.
- Perubahan tampilan Instagram Lite atau LDPlayer dapat mempengaruhi keberhasilan otomasi.
- Jika ingin mengganti emulator, beberapa bagian script (terutama ADB atau path) perlu diubah secara manual.

## Dependencies Utama

- `uiautomator2`
- `adbutils`
- `opencv-python`
- `requests`
- `google-api-python-client`
- `google-auth-oauthlib`
- `google-auth-httplib2`

Tambahkan package Google API secara manual jika belum ada:
```
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

---

**Kontribusi dan saran sangat diterima!**
