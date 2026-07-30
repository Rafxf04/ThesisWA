import requests
import json
import os
from abc import ABC, abstractmethod
from src.config import ConfigManager

class EnrichmentService(ABC):
    @abstractmethod
    def lookup(self, ip_address: str) -> dict:
        pass

class IpApiEnrichment(EnrichmentService):
    """
    Concrete implementation of EnrichmentService using ip-api.com.
    """
    def __init__(self):
        self.base_url = ConfigManager().get("ip_api_url", "http://ip-api.com/json/")

    def lookup(self, ip_address: str) -> dict:
        # Avoid private and local IPs using ipaddress module
        try:
            import ipaddress
            ip_obj = ipaddress.ip_address(ip_address)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast:
                return {"country": "Local", "city": "Local", "org": "Local Network"}
        except ValueError:
            pass
            
        try:
            resp = requests.get(f"{self.base_url}{ip_address}?fields=status,message,country,city,org,as", timeout=1.5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    return {
                        "country": data.get("country", "Unknown"),
                        "city": data.get("city", "Unknown"),
                        "org": data.get("org") or data.get("as", "Unknown")
                    }
        except Exception:
            pass
        return {}


class CacheProxy(EnrichmentService):
    """
    Proxy/Decorator pattern to cache API lookups and reduce network calls.
    """
    def __init__(self, service: EnrichmentService):
        self.service = service
        self.cache_file = ConfigManager().get("cache_file", "enrichment_cache.json")
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f)
        except Exception:
            pass

    def lookup(self, ip_address: str) -> dict:
        if ip_address in self.cache:
            return self.cache[ip_address]

        # Call actual service if not in cache
        result = self.service.lookup(ip_address)
        if result:
            self.cache[ip_address] = result
            # Save incrementally (in a real app, maybe save periodically)
            self._save_cache()
            
        return result
