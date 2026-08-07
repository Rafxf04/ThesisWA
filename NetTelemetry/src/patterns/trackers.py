from collections import defaultdict
from src.patterns.observer import PacketObserver
from src.patterns.domain_categorizer import DomainCategorizer

class StatsTracker(PacketObserver):
    """
    Observer that counts calls per protocol and calculates total bytes.
    """
    def __init__(self):
        self.protocol_counts = defaultdict(int)
        self.protocol_bytes = defaultdict(int)
        self.total_packets = 0

    def on_packet_parsed(self, packet_data: dict):
        proto = packet_data.get("protocol")
        length = packet_data.get("length", 0)
        
        if proto:
            self.protocol_counts[proto] += 1
            self.protocol_bytes[proto] += length
            self.total_packets += 1

    def print_stats(self):
        print("\n--- Protocol Statistics ---")
        print(f"Total Packets Processed: {self.total_packets}")
        for proto, count in sorted(self.protocol_counts.items(), key=lambda x: x[1], reverse=True):
            bytes_total = self.protocol_bytes[proto]
            print(f"Protocol: {proto:<10} | Count: {count:<8} | Bytes: {bytes_total}")


from collections import deque

class FlowTracker(PacketObserver):
    """
    Observer that tracks flows, destination servers, and applies Enrichment.
    """
    def __init__(self, enrichment_service=None, db_repo=None):
        self.enrichment_service = enrichment_service
        self.db_repo = db_repo
        self.flows = deque(maxlen=100)
        self.domain_categorizer = DomainCategorizer()
        self.ip_app_cache = {}

    def on_packet_parsed(self, packet_data: dict):
        # We only care about packets with IPs
        if not packet_data.get("dst_ip"):
            return

        dst_ip = packet_data["dst_ip"]
        tls_sni = packet_data.get("tls_sni")
        dst_port = packet_data.get("dst_port")

        # 1. Primary: Deep Packet Inspection (DPI) from pyshark
        highest_layer = str(packet_data.get("highest_layer", "")).upper()
        base_layers = {"IPV4", "IPV6", "ARP", "ETH", "DATA", "FRAME", "IP", "UNKNOWN", ""}
        
        service_name = "Unknown"
        if highest_layer not in base_layers and highest_layer not in {"TCP", "UDP"}:
            service_name = highest_layer
            
        # 2. Fallback: Basic local service identification via well-known ports
        if service_name == "Unknown":
            service_name = self._guess_service(dst_port)
            if service_name == "Unknown":
                service_name = self._guess_service(packet_data.get("src_port"))
                
            # If still unknown, use transport layer name (TCP/UDP Unclassified)
            if service_name == "Unknown":
                if highest_layer in {"TCP", "UDP"}:
                    service_name = f"{highest_layer} (Unclassified)"
                else:
                    proto = str(packet_data.get("protocol", "")).upper()
                    if proto and proto not in base_layers:
                        service_name = f"{proto} (Unclassified)"
        
        # Basic local app identification via User-Agent and SNI
        http_user_agent = packet_data.get("http_user_agent")
        
        # Enrichment (Geo & ASN/Org via ip-api)
        src_geo_data = {}
        dst_geo_data = {}
        src_ip = packet_data.get("src_ip")
        if self.enrichment_service:
            if src_ip: src_geo_data = self.enrichment_service.lookup(src_ip) or {}
            if dst_ip: dst_geo_data = self.enrichment_service.lookup(dst_ip) or {}

        # Guess Source App & Category
        src_app_name, src_category = self._identify_application(packet_data.get("src_port"), None, None, None)
        
        # Use cache if not found
        if src_app_name == "Unknown" and src_ip in self.ip_app_cache:
            src_app_name, src_category = self.ip_app_cache[src_ip]
            
        if src_app_name == "Unknown" and src_geo_data.get("org"):
            src_app_name = src_geo_data.get("org")
            src_category = "Cloud/Hosting"

        # Guess Destination App & Category
        http_host = packet_data.get("http_host")
        dst_app_name, dst_category = self._identify_application(dst_port, tls_sni, http_user_agent, http_host)
        
        # Cache successful SNI/Host identifications
        if (tls_sni or http_host) and dst_app_name != "Unknown":
            self.ip_app_cache[dst_ip] = (dst_app_name, dst_category)
            
        # Use cache if not found
        if dst_app_name == "Unknown" and dst_ip in self.ip_app_cache:
            dst_app_name, dst_category = self.ip_app_cache[dst_ip]
            
        if dst_app_name == "Unknown" and dst_geo_data.get("org"):
            dst_app_name = dst_geo_data.get("org")
            dst_category = "Cloud/Hosting"

        packet_data["service_name"] = service_name
        packet_data["src_app_name"] = src_app_name
        packet_data["src_category"] = src_category
        packet_data["dst_app_name"] = dst_app_name
        packet_data["dst_category"] = dst_category
        packet_data["geo_country"] = dst_geo_data.get("country", "Unknown") # Keeping main geo as dst
        packet_data["geo_city"] = dst_geo_data.get("city", "Unknown")
        
        # Save or batch flow
        self.flows.append(packet_data)
        
        # If DB repo is configured, export to DB
        if self.db_repo:
            self.db_repo.insert_packet(packet_data)

    def _guess_service(self, port):
        port_map = {
            20: "FTP-DATA",
            21: "FTP",
            22: "SSH",
            23: "TELNET",
            25: "SMTP",
            53: "DNS",
            67: "DHCP/BOOTP",
            68: "DHCP/BOOTP",
            69: "TFTP",
            80: "HTTP",
            110: "POP3",
            123: "NTP",
            137: "NETBIOS-NS",
            138: "NETBIOS-DGM",
            139: "NETBIOS-SSN",
            143: "IMAP",
            161: "SNMP",
            162: "SNMP-TRAP",
            389: "LDAP",
            443: "HTTPS",
            445: "SMB",
            465: "SMTPS",
            514: "SYSLOG",
            587: "SMTP-SUBMISSION",
            636: "LDAPS",
            853: "DNS-OVER-TLS",
            993: "IMAPS",
            995: "POP3S",
            1194: "OPENVPN",
            1433: "MSSQL",
            1521: "ORACLE",
            1723: "PPTP",
            1900: "SSDP",
            3306: "MYSQL",
            3389: "RDP",
            5060: "SIP",
            5061: "SIPS",
            5228: "MTALK / FCM",
            5353: "MDNS",
            5432: "POSTGRESQL",
            6379: "REDIS",
            8080: "HTTP-PROXY",
            8443: "HTTPS-ALT"
        }
        return port_map.get(port, "Unknown")

    def _identify_application(self, port, sni, user_agent, http_host):
        """
        DPI Engine: Returns a tuple (App_Name, Category) based on signatures.
        """
        # 1. Check SNI or HTTP Host (Domain based signatures)
        domain = None
        if sni: domain = sni.lower()
        elif http_host: domain = http_host.lower()
            
        if domain:
            rules = {
                "google": ("Google Services", "Search / Web"),
                "youtube": ("YouTube", "Streaming Media"),
                "ytimg": ("YouTube", "Streaming Media"),
                "gstatic": ("Google Services", "CDN / Web"),
                "facebook": ("Facebook", "Social Media"),
                "fbcdn": ("Meta Services", "CDN / Web"),
                "instagram": ("Instagram", "Social Media"),
                "whatsapp": ("WhatsApp", "Messaging"),
                "netflix": ("Netflix", "Streaming Media"),
                "nflx": ("Netflix", "Streaming Media"),
                "spotify": ("Spotify", "Streaming Media"),
                "apple": ("Apple Services", "Cloud / Web"),
                "icloud": ("Apple iCloud", "Cloud Storage"),
                "aaplimg": ("Apple Services", "CDN / Web"),
                "amazon": ("Amazon Services", "Cloud Infrastructure"),
                "aws": ("AWS", "Cloud Infrastructure"),
                "cloudfront": ("AWS Cloudfront", "CDN / Web"),
                "microsoft": ("Microsoft Services", "Productivity"),
                "azure": ("Microsoft Azure", "Cloud Infrastructure"),
                "windows": ("Microsoft Windows", "OS Updates / Web"),
                "office365": ("Microsoft 365", "Productivity"),
                "live.com": ("Microsoft Live", "Web Services"),
                "skype": ("Skype", "Conferencing"),
                "bing": ("Bing", "Search / Web"),
                "twitter": ("Twitter/X", "Social Media"),
                "twimg": ("Twitter/X", "Social Media"),
                "x.com": ("Twitter/X", "Social Media"),
                "linkedin": ("LinkedIn", "Social Media"),
                "github": ("GitHub", "Developer Tools"),
                "zoom.us": ("Zoom", "Conferencing"),
                "slack": ("Slack", "Productivity / Messaging"),
                "discord": ("Discord", "Gaming / Messaging"),
                "twitch": ("Twitch", "Streaming Media"),
                "ttvnw": ("Twitch", "Streaming Media"),
                "dropbox": ("Dropbox", "Cloud Storage")
            }
            for keyword, (app, category) in rules.items():
                if keyword in domain:
                    return app, category
                    
            # Se non ci sono regole hardcoded, proviamo a usare il database UT1 reale scaricato
            ut1_category = self.domain_categorizer.get_category(domain)
            if ut1_category:
                # Restituiamo il dominio stesso come App e la categoria trovata
                return domain, ut1_category
                
            return domain, "Web Browsing" # Fallback if domain exists but no rule matched

        # 2. Check User Agent (Client based signatures)
        if user_agent:
            agent = user_agent.lower()
            if "chrome" in agent: return "Google Chrome", "Web Browser"
            if "firefox" in agent: return "Mozilla Firefox", "Web Browser"
            if "safari" in agent and "chrome" not in agent: return "Apple Safari", "Web Browser"
            if "curl" in agent: return "cURL", "Developer Tools"
            if "postman" in agent: return "Postman", "Developer Tools"
            return user_agent[:30] + "...", "Web Client"

        # 3. Fallback to Port-based identification for local services
        if port in [53, 67, 68, 137, 138, 139, 1900, 5353]:
            return "Local Network", "Network Services"
            
        return "Unknown", "Unknown"
        
    def print_flows(self, limit=10):
        print(f"\n--- Recent Flows (showing last {limit}) ---")
        for f in list(self.flows)[-limit:]:
            src_str = f'Src: {f.get("src_ip")}:{f.get("src_port")}'
            dst_str = f'Dst: {f.get("dst_ip")}:{f.get("dst_port")}'
            proto = f.get("protocol")
            service = f.get("service_name")
            src_app = f.get("src_app_name")
            src_cat = f.get("src_category", "Unknown")
            dst_app = f.get("dst_app_name")
            dst_cat = f.get("dst_category", "Unknown")
            sni = f.get("tls_sni")
            payload = f.get("payload_preview")
            
            line = f"{src_str} [{src_cat}: {src_app}] | {dst_str} [{dst_cat}: {dst_app}] | Proto: {proto}/{service}"
            if sni: line += f" | SNI: {sni}"
            if payload: line += f" | Payload: {payload}"
            try:
                print(line)
            except UnicodeEncodeError:
                print(line.encode('ascii', errors='backslashreplace').decode('ascii'))
