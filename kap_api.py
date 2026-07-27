from playwright.sync_api import sync_playwright


def test_kap():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        page.goto(
            "https://www.kap.org.tr/tr/bildirim-sorgulari",
            wait_until="networkidle",
            timeout=60000
        )

        print("Sayfa Başlığı:")
        print(page.title())

        page.screenshot(path="kap_home.png")

        input("Tarayıcı açıldı. Devam etmek için Enter'a bas...")

        browser.close()


if __name__ == "__main__":
    test_kap()
