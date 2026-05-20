# 🛍️ PriceSniper - Otomatik Fiyat Takip Aracı

Elektronik ürünlerin fiyatlarını **Geizhals.de** ve **Kleinanzeigen.de** gibi web sitelerinden otomatik olarak takip eden Python uygulaması.

## 📋 Özellikler

✅ **Çoklu Sağlayıcı Desteği**
- Geizhals.de (Resmi elektronik ürün sitesi)
- Kleinanzeigen.de (İkinci el ve yeni ürün pazarı)

✅ **Çoklu Ürün Takibi**
- 8+ ürün için eşzamanlı fiyat kontrolü
- Kolay JSON konfigürasyonu

✅ **Fiyat Uyarıları**
- Min/Max fiyat belirleme
- Otomatik bildirimler

✅ **Zamanlı Çalışma**
- APScheduler ile periyodik kontroller
- Özelleştirilebilir zaman aralıkları

✅ **Bildirim Sistemi**
- Konsol bildirimleri
- Dosyaya kaydetme (alert log)
- Genişletilebilir mimarisi

## 🚀 Kurulum

### 1. Gerekli Bağımlılıkları Yükle
```bash
cd c:\Users\Alp\VSCodeProjects\priceSniper
pip install -r requirements_new.txt
```

### 2. Playwright Tarayıcılarını Yükle
```bash
playwright install chromium
```

## 📁 Proje Yapısı

```
priceSniper/
├── main_orchestrator.py       # Tek çalışma modu
├── main_scheduler.py          # Zamanlı çalışma modu
├── config.json                # Ürün konfigürasyonu
├── requirements_new.txt       # Bağımlılıklar
├── data/
│   ├── pricesniper.db         # SQLite veritabanı
│   └── screenshots/           # Hata durumunda ekran görüntüleri
├── priceSniper/
│   ├── src/
│   │   ├── database/
│   │   │   └── models.py      # SQLAlchemy modelleri
│   │   ├── providers/
│   │   │   ├── geizhals.py    # Geizhals scraper
│   │   │   └── kleinanzeigen.py # Kleinanzeigen scraper
│   │   ├── notifiers/
│   │   │   ├── base.py        # Temel notifier sınıfı
│   │   │   ├── console_notifier.py
│   │   │   └── file_notifier.py
│   │   └── brain/             # AI/LLM entegrasyonu için
│   └── __init__.py
└── README.md
```

## 🎯 Kullanım

### Tek Çalışma Modu
```bash
python main_orchestrator.py
```
Bir kez tüm ürünleri kontrol eder ve çıkar.

### Zamanlı Modu (Önerilen)
```bash
python main_scheduler.py --scheduled
```
Ayarlanmış zaman aralıklarında (default: 60 dakika) otomatik olarak fiyat kontrol eder.

## 🔧 Konfigürasyon (config.json)

```json
{
  "products": [
    {
      "id": 1,
      "name": "NVIDIA RTX 4070",
      "search_query": "RTX 4070",
      "price_alert_min": 450,      // € altında uyarı
      "price_alert_max": 650,      // € üstünde uyarı
      "active": true
    }
  ],
  "settings": {
    "check_interval_minutes": 60,
    "enable_notifications": true,
    "notification_channels": ["console", "file"]
  }
}
```

## 💾 Veritabanı

SQLite kullanılmaktadır (`data/pricesniper.db`):

### products tablosu
- `id` - Ürün ID
- `name` - Ürün adı
- `search_query` - Arama sorgusu

### price_history tablosu
- `id` - Kayıt ID
- `product_id` - Ürünün ID'si
- `source` - Kaynak (Geizhals, Kleinanzeigen)
- `price` - Fiyat (€)
- `url` - Ürün URL'i
- `timestamp` - Kontrol zamanı

## 📊 Örnek Çıktı

```
2026-05-16 20:45:30,123 - INFO - ======================================================================
2026-05-16 20:45:30,124 - INFO - 🕐 Fiyat kontrolü başladı: 2026-05-16 20:45:30
2026-05-16 20:45:30,125 - INFO - ======================================================================

2026-05-16 20:45:30,126 - INFO - 
📦 Ürün işleniyor: NVIDIA RTX 4070
2026-05-16 20:45:30,127 - INFO -   🔍 Geizhals.de taranıyor...
2026-05-16 20:45:35,452 - INFO -   ✅ Geizhals: 549.99€
2026-05-16 20:45:35,453 - INFO -   🔍 Kleinanzeigen.de taranıyor...
2026-05-16 20:45:42,678 - INFO -   ✅ Kleinanzeigen: 499€

======================================================================
📊 FİYAT ÖZETİ
======================================================================

📦 NVIDIA RTX 4070
   Geizhals: 549.99€ (2026-05-16 20:45:35)
   Kleinanzeigen: 499€ (2026-05-16 20:45:42)
```

## ⚙️ İleri Ayarlar

### WebDriver Tespiti Engelleme
Her provider otomatik olarak WebDriver tespitini gizler:
```python
await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
```

### User-Agent Kustomizasyonu
Modern Chrome tarayıcısı olarak tanınır:
```python
user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
```

## 🚨 Sorun Giderme

### Playwright Hatası
```bash
playwright install chromium
```

### Bağlantı Hatası
- İnternet bağlantınızı kontrol edin
- Siteye doğrudan erişip erişemediğinizi test edin

### Fiyat Bulunamadı
- Ürün adını config.json'da kontrol edin
- Siteyi manuel olarak ziyaret edip sayfa yapısını kontrol edin

## 📝 Günlük Log

Tüm işlemler `pricesniper.log` dosyasına kaydedilir ve konsola yazdırılır.

## 🔐 Güvenlik

- `.env` dosyası (varsa) hassas veriler için
- Veritabanı `data/` klasöründe saklanır
- Web scrapingle ilgili etikler dikkatle izlenir

## 🤝 Geliştirme

### Yeni Sağlayıcı Ekleme
`src/providers/` klasöründe yeni bir Python dosyası oluşturun:

```python
from playwright.async_api import async_playwright

class NewProvider:
    async def get_price(self, product_name):
        # Implementasyon
        return (price, url)
```

### Yeni Notifier Ekleme
`src/notifiers/` klasöründe yeni bir notifier oluşturun:

```python
from .base import BaseNotifier

class DiscordNotifier(BaseNotifier):
    def notify(self, message: str):
        # Discord'a gönder
        pass
```

## 📄 Lisans

MIT License

---

**Yapım**: Alp  
**Başlangıç**: 2026-05-16
