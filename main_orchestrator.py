import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from priceSniper.src.database.models import Session, Product, PriceHistory
from priceSniper.src.providers.geizhals import GeizhalsProvider
from priceSniper.src.providers.kleinanzeigen import KleinanzeigenProvider

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CONFIG_FILE = 'config.json'

class PriceSniperOrchestrator:
    def __init__(self):
        self.session = Session()
        self.geizhals = GeizhalsProvider()
        self.kleinanzeigen = KleinanzeigenProvider()
        self.config = self.load_config()

    def load_config(self):
        """Ürünleri config.json'dan yükle"""
        if not Path(CONFIG_FILE).exists():
            logger.warning(f"⚠️ {CONFIG_FILE} bulunamadı. Örnek config oluşturuluyor...")
            self.create_sample_config()
        
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def create_sample_config(self):
        """Örnek konfigürasyon dosyası oluştur"""
        sample_config = {
            "products": [
                {
                    "id": 1,
                    "name": "RTX 4070",
                    "search_query": "RTX 4070",
                    "price_alert_min": 450,
                    "price_alert_max": 600,
                    "active": True
                },
                {
                    "id": 2,
                    "name": "Ryzen 7 9800X3D",
                    "search_query": "Ryzen 7 9800X3D",
                    "price_alert_min": 400,
                    "price_alert_max": 500,
                    "active": True
                },
                {
                    "id": 3,
                    "name": "Intel i9-14900K",
                    "search_query": "Intel i9-14900K",
                    "price_alert_min": 500,
                    "price_alert_max": 700,
                    "active": True
                },
                {
                    "id": 4,
                    "name": "AMD Ryzen 5 7600X",
                    "search_query": "Ryzen 5 7600X",
                    "price_alert_min": 200,
                    "price_alert_max": 300,
                    "active": True
                },
                {
                    "id": 5,
                    "name": "DDR5 32GB RAM",
                    "search_query": "DDR5 32GB",
                    "price_alert_min": 100,
                    "price_alert_max": 200,
                    "active": True
                }
            ],
            "settings": {
                "check_interval_minutes": 60,
                "enable_notifications": True,
                "notification_channels": ["console"]
            }
        }
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Örnek config oluşturuldu: {CONFIG_FILE}")

    def ensure_product_in_db(self, product_config):
        """Ürünü veritabanında kontrol et, yoksa ekle"""
        existing = self.session.query(Product).filter_by(
            search_query=product_config['search_query']
        ).first()
        
        if not existing:
            product = Product(
                name=product_config['name'],
                search_query=product_config['search_query']
            )
            self.session.add(product)
            self.session.commit()
            logger.info(f"✅ Yeni ürün eklendi: {product_config['name']}")
            return product
        
        return existing

    async def scrape_all_products(self):
        """Tüm ürünleri tüm sağlayıcılardan scrap et"""
        logger.info("\n" + "="*60)
        logger.info(f"🕐 Fiyat kontrolü başladı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)
        
        active_products = [p for p in self.config['products'] if p.get('active', True)]
        
        if not active_products:
            logger.warning("❌ Aktif ürün yok!")
            return

        for product_config in active_products:
            logger.info(f"\n📦 Ürün işleniyor: {product_config['name']}")
            
            # Veritabanında emin ol
            product = self.ensure_product_in_db(product_config)
            
            # Geizhals'tan scrape et
            logger.info(f"  🔍 Geizhals.de taranıyor...")
            try:
                geizhals_price = await self.geizhals.get_price(product_config['search_query'])
                if geizhals_price:
                    self.save_price(product, 'Geizhals', geizhals_price, 
                                   f"https://geizhals.de/?fs={product_config['search_query'].replace(' ', '+')}&hloc=de")
                    logger.info(f"  ✅ Geizhals: {geizhals_price}€")
            except Exception as e:
                logger.error(f"  ❌ Geizhals hatası: {e}")

            # Kleinanzeigen'den scrape et
            logger.info(f"  🔍 Kleinanzeigen.de taranıyor...")
            try:
                kleinanzeigen_result = await self.kleinanzeigen.get_price(product_config['search_query'])
                if kleinanzeigen_result:
                    price, url = kleinanzeigen_result
                    self.save_price(product, 'Kleinanzeigen', price, url)
                    logger.info(f"  ✅ Kleinanzeigen: {price}€")
            except Exception as e:
                logger.error(f"  ❌ Kleinanzeigen hatası: {e}")

            # Fiyat uyarıları kontrol et
            self.check_price_alerts(product, product_config)

        logger.info("\n" + "="*60)
        logger.info("✅ Tüm ürünler işlendi!")
        logger.info("="*60 + "\n")

    def save_price(self, product, source, price, url):
        """Fiyat kaydını veritabanına kaydet"""
        price_record = PriceHistory(
            product_id=product.id,
            source=source,
            price=price,
            url=url
        )
        self.session.add(price_record)
        self.session.commit()

    def check_price_alerts(self, product, product_config):
        """Fiyat uyarılarını kontrol et"""
        min_alert = product_config.get('price_alert_min')
        max_alert = product_config.get('price_alert_max')
        
        # Son fiyatları al
        latest_prices = self.session.query(PriceHistory).filter_by(
            product_id=product.id
        ).order_by(PriceHistory.timestamp.desc()).limit(2).all()
        
        for price_record in latest_prices:
            if min_alert and price_record.price < min_alert:
                logger.warning(f"🔴 UYARI: {product.name} fiyatı {min_alert}€'nin altında! "
                             f"({price_record.price}€ @ {price_record.source})")
            if max_alert and price_record.price > max_alert:
                logger.warning(f"⚠️ UYARI: {product.name} fiyatı {max_alert}€'nin üstünde! "
                             f"({price_record.price}€ @ {price_record.source})")

    def print_summary(self):
        """Veritabanında kaydedilen fiyatların özetini yazdır"""
        products = self.session.query(Product).all()
        
        if not products:
            logger.info("📊 Veritabanında ürün yok.")
            return
        
        logger.info("\n" + "="*60)
        logger.info("📊 FİYAT ÖZETİ")
        logger.info("="*60)
        
        for product in products:
            prices = self.session.query(PriceHistory).filter_by(
                product_id=product.id
            ).order_by(PriceHistory.timestamp.desc()).limit(5).all()
            
            if prices:
                logger.info(f"\n📦 {product.name}")
                for price_record in prices:
                    logger.info(f"   {price_record.source}: {price_record.price}€ "
                              f"({price_record.timestamp.strftime('%Y-%m-%d %H:%M:%S')})")
        
        logger.info("="*60 + "\n")

async def main():
    """Ana giriş noktası"""
    orchestrator = PriceSniperOrchestrator()
    
    # Tek bir çalışma
    await orchestrator.scrape_all_products()
    orchestrator.print_summary()

if __name__ == '__main__':
    asyncio.run(main())
