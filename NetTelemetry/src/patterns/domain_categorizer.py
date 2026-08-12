import os
import urllib.request
import time

class DomainCategorizer:
    """
    Singleton-like (o service): Gestisce una cache locale per le categorie dei domini,
    permettendo query veloci senza continue richieste di rete.
    """
    def __init__(self, cache_dir=".domain_cache"):
        """
        Scopo: Inizializza il categorizzatore, preparando le cartelle per la cache e le liste di categorie.

        Parametri:
        - cache_dir (str): Il percorso della cartella cache.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        self.cache_dir = cache_dir
        self.base_url = "https://raw.githubusercontent.com/olbat/ut1-blacklists/master/blacklists/{}/domains"
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
        """
        Scopo: Scarica (se necessario) e carica in memoria (in un dizionario) le blacklist dei domini per le categorie selezionate.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione propagata.
        """
        print("[*] Inizializzazione Domain Categorizer (UT1 Open Source)...")
        for cat_id, cat_name in self.categories_to_fetch.items():
            cache_file = os.path.join(self.cache_dir, f"{cat_id}.txt")
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
        """
        Scopo: Cerca un dominio (ed i suoi sottodomini) nella cache in memoria per determinarne la categoria.

        Parametri:
        - domain (str): Il nome a dominio da analizzare.

        Valore di ritorno:
        - str: Il nome della categoria se trovata, altrimenti None.

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        if not domain:
            return None
        domain = domain.lower()
        if domain in self.domain_map:
            return self.domain_map[domain]
            
        # Controllo per subdominio (es. video.it.facebook.com -> it.facebook.com -> facebook.com)
        parts = domain.split('.')
        for i in range(len(parts) - 1):
            sub_domain = ".".join(parts[i:])
            if sub_domain in self.domain_map:
                return self.domain_map[sub_domain]
                
        return None
