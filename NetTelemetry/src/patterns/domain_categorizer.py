import os
import urllib.request
import time

class DomainCategorizer:
    """
    Downloads and caches open-source domain categorization lists (UT1 blacklists).
    Provides O(1) lookup for categorizing domains extracted from PCAPs.
    """
    def __init__(self, cache_dir=".domain_cache"):
        self.cache_dir = cache_dir
        self.base_url = "https://raw.githubusercontent.com/olbat/ut1-blacklists/master/blacklists/{}/domains"
        
        # Le categorie che vogliamo tracciare come Netify
        self.categories_to_fetch = {
            "social_networks": "Social Media",
            "games": "Gaming",
            "audio-video": "Streaming Media",
            "shopping": "E-Commerce",
            "news": "News / Media",
            "bank": "Financial Services",
            "malware": "Cybersecurity / Malware",
            "phishing": "Cybersecurity / Phishing"
        }
        
        self.domain_map = {}
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
        self._load_domains()
        
    def _load_domains(self):
        print("[*] Inizializzazione Domain Categorizer (UT1 Open Source)...")
        for cat_id, cat_name in self.categories_to_fetch.items():
            cache_file = os.path.join(self.cache_dir, f"{cat_id}.txt")
            
            # Se il file non esiste o è vecchio (es. > 7 giorni), lo scarica
            if not os.path.exists(cache_file) or (time.time() - os.path.getmtime(cache_file)) > 604800:
                print(f"    - Scaricamento database '{cat_name}'...")
                try:
                    url = self.base_url.format(cat_id)
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as response:
                        content = response.read().decode('utf-8')
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                except Exception as e:
                    print(f"      [!] Errore download {cat_id}: {e}")
                    if not os.path.exists(cache_file):
                        # Crea file vuoto per evitare loop di errori
                        with open(cache_file, 'w') as f:
                            pass
            
            # Carica in RAM il dizionario per query O(1)
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        domain = line.strip().lower()
                        if domain and not domain.startswith('#'):
                            self.domain_map[domain] = cat_name
            except Exception as e:
                pass
                
        print(f"[*] Caricati {len(self.domain_map)} domini unici nel motore a regole.")
        
    def get_category(self, domain):
        if not domain:
            return None
        domain = domain.lower()
        # Controllo esatto
        if domain in self.domain_map:
            return self.domain_map[domain]
            
        # Controllo per subdominio (es. video.it.facebook.com -> it.facebook.com -> facebook.com)
        parts = domain.split('.')
        for i in range(len(parts) - 1):
            sub_domain = ".".join(parts[i:])
            if sub_domain in self.domain_map:
                return self.domain_map[sub_domain]
                
        return None
