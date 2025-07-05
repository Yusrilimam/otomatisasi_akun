import os
from mitmproxy import http

# Menentukan lokasi file cookie akan disimpan (di folder yang sama dengan skrip ini)
COOKIE_FILE = os.path.join(os.path.dirname(__file__), "captured_cookies.txt")

class CookieSaver:
    def response(self, flow: http.HTTPFlow) -> None:
        """
        Fungsi ini dijalankan untuk setiap respons server yang dicegat.
        """
        # URL target bisa disesuaikan jika Instagram mengubah endpoint-nya
        # Kita cari URL yang relevan dengan pembuatan atau login akun
        target_urls = [
            "i.instagram.com/api/v1/accounts/create/",
            "i.instagram.com/api/v1/accounts/login/"
        ]

        # Cek apakah URL permintaan cocok dan ada header 'set-cookie' di respons
        if any(url in flow.request.pretty_url for url in target_urls) and "set-cookie" in flow.response.headers:
            all_cookies = flow.response.headers.get_all("set-cookie")
            cookie_string = "; ".join(all_cookies)

            print(f"\n\n✅ --- COOKIE INSTAGRAM DITEMUKAN! --- ✅")
            print(f"URL: {flow.request.pretty_url}")
            print(f"Cookies: {cookie_string}")

            # Simpan cookie ke file, menimpa file yang mungkin ada sebelumnya
            with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                f.write(cookie_string)

            print(f"🍪 Cookie telah disimpan ke file {COOKIE_FILE}\n\n")

# Mendaftarkan addon agar bisa dijalankan oleh mitmproxy
addons = [CookieSaver()]