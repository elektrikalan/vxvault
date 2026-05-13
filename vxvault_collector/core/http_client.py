import requests
import urllib3
from config import VERIFY_SSL, TIMEOUT, LOGIN_URL, PASSWORD, DOWNLOAD_USER, DOWNLOAD_PASS, DOWNLOAD_DIR
import os

urllib3.disable_warnings()

class HTTPClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def login(self):
        print(f"[*] Giriş yapılıyor: {LOGIN_URL}")
        data = {"password": PASSWORD}
        response = self.post(LOGIN_URL, data=data)
        if response and "VXVault" in response.text:
            print("[+] Giriş başarılı.")
            return True
        print("[-] Giriş başarısız.")
        return False

    def get(self, url):
        try:
            response = self.session.get(url, timeout=TIMEOUT, verify=VERIFY_SSL)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"[-] HTTP GET hatası ({url}): {e}")
            return None

    def post(self, url, data=None):
        try:
            response = self.session.post(url, data=data, timeout=TIMEOUT, verify=VERIFY_SSL)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"[-] HTTP POST hatası ({url}): {e}")
            return None

    def download_file(self, url, filename):
        try:
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            
            if os.path.exists(filepath):
                return True

            response = self.session.get(
                url, 
                auth=(DOWNLOAD_USER, DOWNLOAD_PASS), 
                timeout=TIMEOUT, 
                verify=VERIFY_SSL,
                stream=True
            )
            response.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"[+] İndirildi: {filename}")
            return True
        except Exception as e:
            print(f"[-] İndirme hatası ({filename}): {e}")
            return False
