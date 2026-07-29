import threading
import json
import os

class ConfigManager:
    """
    Singleton class for managing application configuration.
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
        self.config = {
            "questdb_host": os.environ.get("QUESTDB_HOST", "127.0.0.1"),
            "questdb_port": int(os.environ.get("QUESTDB_PORT", 9009)), # Default to ILP port 9009
            "questdb_ilp_port": int(os.environ.get("QUESTDB_ILP_PORT", 9009)),
            "questdb_http_port": int(os.environ.get("QUESTDB_HTTP_PORT", 9000)),
            "ip_api_url": "http://ip-api.com/json/",
            "cache_file": "enrichment_cache.json"
        }
        
    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

