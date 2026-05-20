from abc import ABC, abstractmethod
from datetime import datetime

class BaseNotifier(ABC):
    """Tüm notifier'ların implement etmesi gereken temel sınıf"""
    
    @abstractmethod
    def notify(self, message: str):
        """Bildirim gönder"""
        pass
