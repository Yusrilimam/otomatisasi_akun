# Otomatisasi Instalasi & Pembuatan Akun Instagram Lite di Mumu Player

Proyek ini bertujuan untuk mengotomatisasi proses instalasi Instagram Lite dan pembuatan akun secara otomatis di emulator Mumu Player menggunakan Python.

## Fitur Utama
- Instalasi otomatis Instagram Lite APK di emulator Mumu Player.
- Pembuatan akun Instagram secara otomatis.
- Integrasi dengan Gmail API (untuk verifikasi email saat pembuatan akun).
- Logging dan error handling.

## Struktur Folder & File Utama

- `main.py`  
  Script utama yang menjalankan seluruh proses otomasi, mulai dari instalasi, registrasi akun, hingga logging.
- `gmail_api_utils.py`  
  Utilitas untuk mengakses Gmail API, digunakan dalam proses verifikasi email saat pembuatan akun Instagram.
- `requirements.txt`  
  Daftar dependencies Python yang diperlukan untuk menjalankan proyek ini.

## Persiapan

1. Pastikan [Mumu Player](https://ldplayer.net) sudah terpasang di komputer Anda.
2. Instal Python 3.x.
3. Aktifkan Gmail API dan unduh credentials jika ingin menggunakan fitur verifikasi email.
4. Jalankan perintah berikut untuk menginstal dependencies:
    ```
    pip install -r requirements.txt
    ```

## Menjalankan Otomasi

```
python main.py
```

Pastikan emulator sudah berjalan sebelum menjalankan script.

## Contoh Output

Setelah script dijalankan, Anda akan melihat log proses instalasi dan pembuatan akun pada terminal/console. Informasi detail juga dapat ditemukan di file log yang dihasilkan (jika ada).

## Catatan
- Proyek ini hanya untuk pembelajaran dan riset otomasi. Pastikan mematuhi terms of service Instagram.
- Gunakan email valid untuk proses verifikasi.
- Otomatisasi ini mungkin tidak selalu berhasil jika ada perubahan pada aplikasi Instagram Lite atau emulator.

---

**Kontribusi dan saran sangat diterima!**
