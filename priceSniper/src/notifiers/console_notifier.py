from datetime import datetime
from .base import BaseNotifier

class ConsoleNotifier(BaseNotifier):
    """Konsola bildirim gönder"""
    
    def notify(self, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] 🔔 {message}")
