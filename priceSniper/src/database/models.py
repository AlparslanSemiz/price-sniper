import os
import datetime
# Doğru importlar buradan gelmeli:
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String)           # Ürünün genel adı (Örn: RTX 4070)
    search_query = Column(String)   # Sitede aratacağımız tam metin

class PriceHistory(Base):
    __tablename__ = 'price_history'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id')) 
    source = Column(String)         # Nereden bulundu? (geizhals, kleinanzeigen)
    price = Column(Float)
    url = Column(String)
    # 'default' ekleyerek zamanın otomatik kaydedilmesini sağlıyoruz:
    timestamp = Column(DateTime, default=datetime.datetime.utcnow) 

# Veritabanı klasörünü kontrol et, yoksa oluştur
if not os.path.exists('data'):
    os.makedirs('data')

# Veritabanına bağlan ve tabloları oluştur
engine = create_engine('sqlite:///data/pricesniper.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

print("✅ Veritabanı başarıyla oluşturuldu ve bağlantı sağlandı.")