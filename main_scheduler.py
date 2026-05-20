import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from priceSniper.src.database.models import Session, Product, PriceHistory
from priceSniper.src.providers.geizhals import GeizhalsProvider
from priceSniper.src.providers.kleinanzeigen import KleinanzeigenProvider
from priceSniper.src.notifiers.console_notifier import ConsoleNotifier
from priceSniper.src.notifiers.file_notifier import FileNotifier

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pricesniper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CONFIG_FILE = 'config.json'

class PriceSniperOrchestrator:
    def __init__(self):
        self.session = Session()
        self.geizhals = GeizhalsProvider()
        self.kleinanzeigen = KleinanzeigenProvider()
        self.config = self.load_config()
        self.notifiers = self.setup_notifiers()
        self.scheduler = None

    def load_config(self):
        """Ürünleri config.json'dan yükle"""
        if not Path(CONFIG_FILE).exists():
            logger.error(f"❌ {CONFIG_FILE} bulunamadı!")
            raise FileNotFoundError(f"{CONFIG_FILE} dosyası gereklidir.")
        
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def setup_notifiers(self):
        """Notifier'ları konfigure et"""
        notifiers = []
        
        if self.config.get('settings', {}).get('enable_notifications'):
            for channel in self.config.get('settings', {}).get('notification_channels', []):
                if channel == 'console':
                    notifiers.append(ConsoleNotifier())
                elif channel == 'file':
                    notifiers.append(FileNotifier())
        
        return notifiers

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
        logger.info("\n" + "="*70)
        logger.info(f"🕐 Fiyat kontrolü başladı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70)
        
        active_products = [p for p in self.config['products'] if p.get('active', True)]
        
        if not active_products:
            logger.warning("❌ Aktif ürün yok!")
            return

        for product_config in active_products:
            logger.info(f"\n📦 Ürün işleniyor: {product_config['name']}")
            
            # Veritabanında emin ol
            product = self.ensure_product_in_db(product_config)
            
            # Geizhals'tan scrape et
            if self.config.get('providers', {}).get('geizhals', {}).get('enabled', True):
                logger.info(f"  🔍 Geizhals.de taranıyor...")
                try:
                    geizhals_price = await self.geizhals.get_price(product_config['search_query'])
                    if geizhals_price:
                        url = f"https://geizhals.de/?fs={product_config['search_query'].replace(' ', '+')}&hloc=de"
                        self.save_price(product, 'Geizhals', geizhals_price, url)
                        logger.info(f"  ✅ Geizhals: {geizhals_price}€")
                except Exception as e:
                    logger.error(f"  ❌ Geizhals hatası: {e}")

            # Kleinanzeigen'den scrape et
            if self.config.get('providers', {}).get('kleinanzeigen', {}).get('enabled', True):
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

        logger.info("\n" + "="*70)
        logger.info("✅ Tüm ürünler işlendi!")
        logger.info("="*70 + "\n")

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
            alert_msg = None
            
            if min_alert and price_record.price < min_alert:
                alert_msg = f"🔴 UYARI: {product.name} fiyatı {min_alert}€'nin altında! ({price_record.price}€ @ {price_record.source}) - {price_record.url}"
                logger.warning(alert_msg)
            
            if max_alert and price_record.price > max_alert:
                alert_msg = f"⚠️ UYARI: {product.name} fiyatı {max_alert}€'nin üstünde! ({price_record.price}€ @ {price_record.source}) - {price_record.url}"
                logger.warning(alert_msg)
            
            if alert_msg:
                for notifier in self.notifiers:
                    notifier.notify(alert_msg)

    def print_summary(self):
        """Veritabanında kaydedilen fiyatların özetini yazdır"""
        products = self.session.query(Product).all()
        
        if not products:
            logger.info("📊 Veritabanında ürün yok.")
            return
        
        logger.info("\n" + "="*70)
        logger.info("📊 FİYAT ÖZETİ")
        logger.info("="*70)
        
        for product in products:
            prices = self.session.query(PriceHistory).filter_by(
                product_id=product.id
            ).order_by(PriceHistory.timestamp.desc()).limit(3).all()
            
            if prices:
                logger.info(f"\n📦 {product.name}")
                for price_record in prices:
                    logger.info(f"   {price_record.source}: {price_record.price}€ "
                              f"({price_record.timestamp.strftime('%Y-%m-%d %H:%M:%S')})")
        
        logger.info("="*70 + "\n")

    def start_scheduler(self):
        """Zamanlayıcıyı başlat"""
        check_interval = self.config.get('settings', {}).get('check_interval_minutes', 60)
        
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(
            self._run_scraper,
            IntervalTrigger(minutes=check_interval),
            id='price_check',
            name=f'Price check every {check_interval} minutes',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"✅ Zamanlayıcı başladı. Her {check_interval} dakikada fiyat kontrolü yapılacak.")

    def _run_scraper(self):
        """Zamanlayıcı tarafından çağrılan scraper"""
        try:
            asyncio.run(self.scrape_all_products())
            self.print_summary()
        except Exception as e:
            logger.error(f"❌ Scheduler hatası: {e}")

    def stop_scheduler(self):
        """Zamanlayıcıyı durdur"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("✅ Zamanlayıcı durduruldu.")

async def main():
    """Ana giriş noktası - tek çalışma"""
    orchestrator = PriceSniperOrchestrator()
    await orchestrator.scrape_all_products()
    orchestrator.print_summary()

async def main_scheduled():
    """Zamanlı çalışma modu"""
    orchestrator = PriceSniperOrchestrator()
    orchestrator.start_scheduler()
    
    try:
        # Zamanlanmış görevleri çalıştırmak için sonsuz döngüde kal
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Interrupt alındı, durduruluyor...")
        orchestrator.stop_scheduler()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--scheduled':
        # Zamanlı mod: Her X dakikada bir fiyat kontrolü
        asyncio.run(main_scheduled())
    else:
        # Tek çalışma modu
        asyncio.run(main())
