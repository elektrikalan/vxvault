import sys
import os

# Projenin kök dizinini sys.path'e ekleyelim
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.http_client import HTTPClient
from collectors.vxvault import VXVaultCollector
from parsers.vxvault_parser import parse
from storage.sqlite import SQLiteStore
from config import BASE_URL

from app.gui import VXVaultGUI

def main():
    app = VXVaultGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
