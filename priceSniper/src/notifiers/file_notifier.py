from datetime import datetime
from .base import BaseNotifier

class FileNotifier(BaseNotifier):
    """Dosyaya bildirim kaydet"""
    
    def __init__(self, filename='alerts.log'):
        self.filename = filename
    
    def notify(self, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.filename, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"✅ Alert kaydedildi: {self.filename}")
