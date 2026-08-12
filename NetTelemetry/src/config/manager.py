import threading
import json
import os

class ConfigManager:
    """
    Singleton Pattern: Gestisce centralmente la configurazione dell'applicazione,
    come le porte e gli host per il database e i servizi di arricchimento.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ConfigManager, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Scopo: Inizializza le variabili di configurazione di default al primo caricamento del Singleton.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        self.config = {
            "questdb_host": os.environ.get("QUESTDB_HOST", "127.0.0.1"),
            "questdb_port": int(os.environ.get("QUESTDB_PORT", 9009)),
            "questdb_ilp_port": int(os.environ.get("QUESTDB_ILP_PORT", 9009)),
            "questdb_http_port": int(os.environ.get("QUESTDB_HTTP_PORT", 9000)),
            "ip_api_url": "http://ip-api.com/json/",
            "cache_file": "enrichment_cache.json"
        }
        
    def get(self, key, default=None):
        """
        Scopo: Recupera un valore di configurazione.

        Parametri:
        - key (str): La chiave della configurazione.
        - default (Any): Valore di default se la chiave non esiste.

        Valore di ritorno:
        - Any: Il valore configurato o il default.

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        return self.config.get(key, default)

    def set(self, key, value):
        """
        Scopo: Imposta un nuovo valore di configurazione in memoria.

        Parametri:
        - key (str): Chiave di configurazione da impostare.
        - value (Any): Valore da assegnare.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        self.config[key] = value
