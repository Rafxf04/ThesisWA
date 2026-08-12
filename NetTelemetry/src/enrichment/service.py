import requests
import json
import os
from abc import ABC, abstractmethod
from src.config import ConfigManager

class EnrichmentService(ABC):
    @abstractmethod
    def lookup(self, ip_address: str) -> dict:
        """
        Scopo: Interfaccia per il recupero delle informazioni di geolocalizzazione o metadata di un IP.

        Parametri:
        - ip_address (str): L'indirizzo IP da ricercare.

        Valore di ritorno:
        - dict: Un dizionario contenente le informazioni (es. country, city, org).

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        pass

class IpApiEnrichment(EnrichmentService):
    """
    Concrete implementation of EnrichmentService using ip-api.com.
    """
    def __init__(self):
        """
        Scopo: Inizializza il servizio di arricchimento con l'URL configurato per ip-api.com.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        self.base_url = ConfigManager().get("ip_api_url", "http://ip-api.com/json/")

    def lookup(self, ip_address: str) -> dict:
        """
        Scopo: Interroga le API di ip-api per ottenere la country, la city e l'organization associate all'IP.

        Parametri:
        - ip_address (str): L'indirizzo IP.

        Valore di ritorno:
        - dict: Dizionario con le informazioni trovate, o un dizionario vuoto se fallisce.

        Eccezioni:
        - Nessuna eccezione propagata (eventuali errori HTTP vengono soppressi).
        """
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
        """
        Scopo: Inizializza il proxy caricando la cache dal disco e salvando il riferimento al servizio sottostante.

        Parametri:
        - service (EnrichmentService): Il servizio reale da wrappare.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        self.service = service
        self.cache_file = ConfigManager().get("cache_file", "enrichment_cache.json")
        self.cache = self._load_cache()
        self.dirty_count = 0

    def _load_cache(self) -> dict:
        """
        Scopo: Carica la cache degli IP dal file JSON se esistente.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - dict: Il dizionario cache caricato o uno vuoto.

        Eccezioni:
        - Nessuna eccezione propagata.
        """
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_cache(self):
        """
        Scopo: Salva la cache corrente su disco per persisterla tra le esecuzioni.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione propagata.
        """
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f)
            self.dirty_count = 0
        except Exception:
            pass

    def lookup(self, ip_address: str) -> dict:
        """
        Scopo: Recupera i dati dell'IP dalla cache; se non presenti, interroga il servizio reale e memorizza il risultato.

        Parametri:
        - ip_address (str): L'IP da ricercare.

        Valore di ritorno:
        - dict: Le informazioni recuperate (dalla cache o dall'API).

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        if ip_address in self.cache:
            return self.cache[ip_address]

        result = self.service.lookup(ip_address)
        if result:
            self.cache[ip_address] = result
            self.dirty_count += 1
            if self.dirty_count >= 50:
                self._save_cache()
            
        return result
        
    def flush(self):
        """
        Scopo: Forza il salvataggio su disco della cache se ci sono state modifiche (chiamato alla fine dell'elaborazione).

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        if self.dirty_count > 0:
            self._save_cache()
