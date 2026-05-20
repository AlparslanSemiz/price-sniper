import asyncio
import os
import re
from playwright.async_api import async_playwright

class KleinanzeigenProvider:
    def __init__(self):
        if not os.path.exists('data'):
            os.makedirs('data')

    async def get_price(self, product_name):
        """
        Kleinanzeigen.de'de ürün ara ve en düşük fiyatı getir.
        Türkiye kategorisinde arama yapar.
        
        Returns:
            Tuple[float, str] or None: (price, url) veya None
        """
        query = product_name.replace(' ', '+')
        search_url = f"https://www.kleinanzeigen.de/s-{query}/c0p"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            # WebDriver gizleme
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            try:
                print(f"📡 Kleinanzeigen'de {product_name} aranıyor...")
                await page.goto(search_url, wait_until="domcontentloaded")

                # Çerez kabulü (eğer varsa)
                try:
                    await page.get_by_role("button", name=re.compile("Accept|Akzeptieren", re.IGNORECASE)).click(timeout=2000)
                    print("✅ Çerezler kabul edildi.")
                except:
                    pass

                await page.wait_for_timeout(2000)
                await page.screenshot(path="data/kleinanzeigen_last_check.png")

                # Sayfadaki tüm metni oku
                page_text = await page.locator("body").inner_text()
                lines = page_text.split('\n')

                print("🔍 Ekranda fiyat aranıyor...")

                # En düşük fiyatı bul
                lowest_price = None
                lowest_url = None

                # Tüm ilanları al
                listings = await page.locator("a.result-item").all()
                
                for listing in listings[:10]:  # İlk 10 ilandan kontrol et
                    try:
                        # Fiyat bilgisini al
                        price_elem = listing.locator(".ad-price")
                        price_text = await price_elem.inner_text()
                        
                        # URL'i al
                        url = await listing.get_attribute("href")
                        if not url.startswith("http"):
                            url = "https://www.kleinanzeigen.de" + url

                        # Fiyatı parse et
                        # "399 €" veya "ab 399 €" formatında olabilir
                        price_match = re.search(r'(\d{1,5}(?:\.\d{3})*)\s*€', price_text)
                        if price_match:
                            price_str = price_match.group(1).replace('.', '')
                            price = float(price_str)
                            
                            # En düşük fiyatı güncelle
                            if lowest_price is None or price < lowest_price:
                                lowest_price = price
                                lowest_url = url
                                print(f"🎯 İlan bulundu: {price}€ - {url}")
                    except Exception as e:
                        continue

                if lowest_price:
                    print(f"✅ En düşük fiyat: {lowest_price}€")
                    await browser.close()
                    return (lowest_price, lowest_url)
                else:
                    print("⚠️ Fiyat bilgisi bulunamadı.")
                    await browser.close()
                    return None

            except Exception as e:
                print(f"❌ Hata: {e}")
                await browser.close()
                return None

if __name__ == "__main__":
    provider = KleinanzeigenProvider()
    result = asyncio.run(provider.get_price("RTX 4070"))
    if result:
        price, url = result
        print(f"Bulunan ürün: {price}€ - {url}")
