import asyncio
import os
import re
from playwright.async_api import async_playwright

class GeizhalsProvider:
    def __init__(self):
        if not os.path.exists('data'):
            os.makedirs('data')

    async def get_price(self, product_name):
        query = product_name.replace(' ', '+')
        search_url = f"https://geizhals.de/?fs={query}&hloc=de"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False) 
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            # Manuel WebDriver Gizleme
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            try:
                print(f"📡 {product_name} için piyasa taranıyor...")
                await page.goto(search_url, wait_until="domcontentloaded")

                # 1. Çerez Geçişi
                try:
                    await page.get_by_role("button", name="Ablehnen").click(timeout=3000)
                    print("✅ Çerezler reddedildi.")
                except:
                    pass

                await page.wait_for_timeout(2500)
                await page.screenshot(path="data/last_check.png")
                
                # 2. METİN TABANLI AV (DOM'u boşver, yazıları oku)
                # Sayfadaki tüm görünür metni satır satır çekiyoruz
                page_text = await page.locator("body").inner_text()
                lines = page_text.split('\n')

                print("🔍 Ekranda fiyat aranıyor...")

                for i, line in enumerate(lines):
                    # Satırda bizim işlemcinin adı geçiyor mu?
                    if product_name.lower() in line.lower():
                        
                        # İşlemciyi bulduk! Şimdi altındaki 15 satıra bakıp '€' arıyoruz
                        for j in range(1, 15):
                            if i + j < len(lines) and "€" in lines[i + j]:
                                price_line = lines[i + j]
                                
                                # Regex ile "ab € 399,86" içinden "399,86" sayısını cımbızla
                                match = re.search(r'€\s*(\d{1,3}(?:\.\d{3})*,\d{2})', price_line)
                                if match:
                                    # Sayıyı float'a (matematiksel değere) çevir
                                    clean_num = match.group(1).replace('.', '').replace(',', '.')
                                    price = float(clean_num)
                                    
                                    # 300 Euro'dan ucuzsa soğutucudur, atla. Değilse doğru fiyattır!
                                    if price > 300:
                                        print(f"🎯 HEDEF VURULDU! Model: {line[:40]}... -> Fiyat: {price} €")
                                        await browser.close()
                                        return price

                print("⚠️ Fiyat satırı bulunamadı.")
                await browser.close()
                return None

            except Exception as e:
                print(f"❌ Hata: {e}")
                await browser.close()
                return None

if __name__ == "__main__":
    bot = GeizhalsProvider()
    asyncio.run(bot.get_price("Ryzen 7 9800X3D"))