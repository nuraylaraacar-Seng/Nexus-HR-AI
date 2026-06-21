"""
Cache Layer: Redis-backed result caching with safe fallback.
Redis bağlantısı yoksa veya başarısız olursa sistem cache'siz çalışmaya devam eder
— hiçbir endpoint Redis'in varlığına bağımlı değildir.
---
Önbellek Katmanı: Güvenli geri dönüşlü Redis tabanlı sonuç önbellekleme.
Redis bağlantısı yoksa ya da başarısız olursa sistem önbelleksiz çalışmaya devam eder.
"""

import os
import json
import logging
from typing import Optional, Any

try:
    import redis
    _REDIS_AVAILABLE=True
except ImportError:
    redis=None
    _REDIS_AVAILABLE=False


class CacheLayer:
    """
    Tek bir Redis clien'ı sarmalar (warpper). Bağlantı kurulmazsa
    veya herhangi bir operasyon başarısız olursa exception fırlatmaz
    None/no-op döner.
    Bu sayede cache, sistemin doğruluğu için değil sadece hızı 
    için bir katman olur.
    """
    
    def __init__(self):
        self.enabled=False
        self._client=None 
        
        redis_url=os.getenv("REDIS_URL")
        if not _REDIS_AVAILABLE:
            logging.info("Redis kütüphanesi yok — cache disabled")
            return
        if not redis_url:
            logging.info("REDIS_URL tanımlı değil — cache devre dışı.")
            return
        try:
            #bağlantı açıldı mı onu kontrol ediyoruz
            self._client=redis.from_url(
                redis_url,
                socket_connect_timeout=2,
                ##2 saniye içinde bağlanmazsa vazgec
                socket_timeout=2,
                decode_responses=True,
            )
            #karşı taraf yaşıyor mu yani redis ona bakıyoruz?(ping)
            #cevap geldi->evet oradayım(pong)
            self._client.ping()
            self.enabled=True
            logging.info("Redis cache Bağlantısı Kuruldu 🎉")

        except Exception as e:
            logging.warning(f"Redis bağğlantısı kurulamadı, cache devre Dışı: {e}")
            self._client=None
            self.enabled=False
    
    def get(self, key: str) -> Optional[Any]:
        """Cache'ten değer okur. Herhangi bir tip dönebilir, yoksa/hata varsa None."""
        if not self.enabled:
            return None 
        
        try:
            raw=self._client.get(key)
            return json.loads(raw) if raw else None
        except Exception as e:
            logging.warning(f"Cache okuma hatası ({key}): {e}")
            return None
    
    
    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> None:
        """Anahtarı kaydeder, ttl_seconds sonra otomatik silinir."""
        if not self.enabled:
            return
        try:
            self._client.setex(key, ttl_seconds, json.dumps(value, default=str))
        except Exception as e:
            logging.warning(f"Cache yazma hatası ({key}): {e}")
    
    def delete_prefix(self, prefix: str)->None:
        """Bir session silindiğinde o session'a ait tüm 
        cache anahtarlarını temizler."""
        if not self.enabled:
            return
        try:
            pipe = self._client.pipeline()
            for key in self._client.scan_iter(match=f"{prefix}*"):
                pipe.delete(key)
            pipe.execute()
        except Exception as e: 
            logging.warning(f"Cache temizleme hatası ({prefix}): {e}")
# Modül seviyesinde tek instance — main.py bunu import edip kullanır.
cache=CacheLayer()
