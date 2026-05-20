"""
Basit test scripti - Yapının doğru kurulduğunu kontrol et
"""

import sys
import os

def check_structure():
    """Proje yapısını kontrol et"""
    print("🔍 PriceSniper yapısı kontrol ediliyor...\n")
    
    required_files = [
        'config.json',
        'main_orchestrator.py',
        'main_scheduler.py',
        'README.md',
        'requirements_new.txt',
        'priceSniper/src/database/models.py',
        'priceSniper/src/providers/geizhals.py',
        'priceSniper/src/providers/kleinanzeigen.py',
        'priceSniper/src/notifiers/base.py',
        'priceSniper/src/notifiers/console_notifier.py',
        'priceSniper/src/notifiers/file_notifier.py',
    ]
    
    missing = []
    for file in required_files:
        path = os.path.join(os.path.dirname(__file__), file)
        if os.path.exists(path):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing.append(file)
    
    if missing:
        print(f"\n⚠️ {len(missing)} dosya eksik!")
        return False
    else:
        print(f"\n✅ Tüm dosyalar bulundu!")
        return True

def check_imports():
    """Ana modülleri import etmeyi dene"""
    print("\n🔍 Import kontrolü yapılıyor...\n")
    
    try:
        from priceSniper.src.database.models import Product, PriceHistory
        print("✅ Database models")
    except Exception as e:
        print(f"❌ Database models: {e}")
        return False
    
    try:
        from priceSniper.src.providers.geizhals import GeizhalsProvider
        print("✅ GeizhalsProvider")
    except Exception as e:
        print(f"❌ GeizhalsProvider: {e}")
        return False
    
    try:
        from priceSniper.src.providers.kleinanzeigen import KleinanzeigenProvider
        print("✅ KleinanzeigenProvider")
    except Exception as e:
        print(f"❌ KleinanzeigenProvider: {e}")
        return False
    
    try:
        from priceSniper.src.notifiers.console_notifier import ConsoleNotifier
        from priceSniper.src.notifiers.file_notifier import FileNotifier
        print("✅ Notifiers")
    except Exception as e:
        print(f"❌ Notifiers: {e}")
        return False
    
    print("\n✅ Tüm importlar başarılı!")
    return True

def check_config():
    """config.json'u kontrol et"""
    print("\n🔍 Config kontrol ediliyor...\n")
    
    import json
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        products = config.get('products', [])
        settings = config.get('settings', {})
        
        print(f"✅ Config başarıyla yüklendi")
        print(f"   📦 Ürün sayısı: {len(products)}")
        print(f"   ⏱️  Kontrol aralığı: {settings.get('check_interval_minutes', 'N/A')} dakika")
        print(f"   🔔 Bildirim: {'✅ Aktif' if settings.get('enable_notifications') else '❌ Kapalı'}")
        
        for i, product in enumerate(products[:3], 1):
            print(f"\n   Ürün {i}: {product.get('name')}")
            print(f"      - Arama: {product.get('search_query')}")
            print(f"      - Min alert: {product.get('price_alert_min')}€")
            print(f"      - Max alert: {product.get('price_alert_max')}€")
        
        if len(products) > 3:
            print(f"\n   ... ve {len(products) - 3} ürün daha")
        
        return True
    except Exception as e:
        print(f"❌ Config hatası: {e}")
        return False

def main():
    print("=" * 60)
    print("🛍️ PriceSniper - Proje Yapısı Test")
    print("=" * 60)
    
    results = []
    
    # Dosya yapısı
    results.append(("Dosya Yapısı", check_structure()))
    
    # Config
    results.append(("Config Dosyası", check_config()))
    
    # Import
    results.append(("Module Imports", check_imports()))
    
    # Özet
    print("\n" + "=" * 60)
    print("📊 TEST ÖZETI")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TÜM TESTLER BAŞARILI!")
        print("\nŞimdi şu komutları çalıştırabilirsiniz:")
        print("\n1. Tek çalışma modu:")
        print("   python main_orchestrator.py")
        print("\n2. Zamanlı modu (önerilen):")
        print("   python main_scheduler.py --scheduled")
        print("\n3. Bağımlılıkları yükle (eğer henüz yapılmadıysa):")
        print("   pip install -r requirements_new.txt")
        print("   playwright install chromium")
    else:
        print("❌ Bazı testler başarısız oldu!")
        sys.exit(1)
    print("=" * 60)

if __name__ == '__main__':
    main()
