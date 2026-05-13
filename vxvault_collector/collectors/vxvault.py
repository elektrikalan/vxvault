from config import LIST_URL, ITEMS_PER_PAGE, BASE_URL

class VXVaultCollector:
    def __init__(self, client):
        self.client = client

    def fetch(self, offset):
        url = f"{LIST_URL}?s={offset}&m={ITEMS_PER_PAGE}"
        response = self.client.get(url)
        return response.text if response else None

    def fetch_details(self, details_id):
        url = f"{BASE_URL}/ViriFiche.php?ID={details_id}"
        response = self.client.get(url)
        return response.text if response else None

    def search_hash(self, hash_str):
        # ViriList.php araması POST isteği gerektirir
        url = f"{BASE_URL}/ViriList.php"
        data = {"MD5": hash_str}
        response = self.client.post(url, data=data)
        return response.text if response else None
