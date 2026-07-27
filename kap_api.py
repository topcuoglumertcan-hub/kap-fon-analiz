import requests


class KAPClient:

    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.kap.org.tr/tr/bildirim-sorgulari"
        })

    def test_connection(self):

        url = "https://www.kap.org.tr/tr/api/disclosures"

        response = self.session.get(url, timeout=20)

        print("Status Code :", response.status_code)

        print(response.text[:500])


if __name__ == "__main__":

    client = KAPClient()

    client.test_connection()
