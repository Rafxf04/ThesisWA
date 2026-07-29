from collections import defaultdict
from src.patterns.observer import PacketObserver

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


class FlowTracker(PacketObserver):
    """
    Observer that tracks flows, destination servers, and applies Enrichment.
    """
    def __init__(self, enrichment_service=None, db_repo=None):
        self.enrichment_service = enrichment_service
        self.db_repo = db_repo
        self.flows = []

    def on_packet_parsed(self, packet_data: dict):
        # We only care about packets with IPs
        if not packet_data.get("dst_ip"):
            return

        dst_ip = packet_data["dst_ip"]
        tls_sni = packet_data.get("tls_sni")
        dst_port = packet_data.get("dst_port")

        # Basic local service identification via well-known ports
        service_name = self._guess_service(dst_port)
        if service_name == "Unknown":
             # Try src_port as well
             service_name = self._guess_service(packet_data.get("src_port"))
        
        # Basic local app identification via User-Agent and SNI
        http_user_agent = packet_data.get("http_user_agent")
        
        # Enrichment (Geo & ASN/Org via ip-api)
        src_geo_data = {}
        dst_geo_data = {}
        if self.enrichment_service:
            src_ip = packet_data.get("src_ip")
            if src_ip: src_geo_data = self.enrichment_service.lookup(src_ip) or {}
            if dst_ip: dst_geo_data = self.enrichment_service.lookup(dst_ip) or {}

        # Guess Source App
        src_app_name = self._guess_app(packet_data.get("src_port"), None, None)
        if src_app_name == "Unknown" and src_geo_data.get("org"):
            src_app_name = src_geo_data.get("org")

        # Guess Destination App
        dst_app_name = self._guess_app(dst_port, tls_sni, http_user_agent)
        if dst_app_name == "Unknown" and dst_geo_data.get("org"):
            dst_app_name = dst_geo_data.get("org")

        packet_data["service_name"] = service_name
        packet_data["src_app_name"] = src_app_name
        packet_data["dst_app_name"] = dst_app_name
        packet_data["geo_country"] = dst_geo_data.get("country", "Unknown") # Keeping main geo as dst
        packet_data["geo_city"] = dst_geo_data.get("city", "Unknown")
        
        # Save or batch flow
        self.flows.append(packet_data)
        
        # If DB repo is configured, export to DB
        if self.db_repo:
            self.db_repo.insert_packet(packet_data)

    def _guess_service(self, port):
        port_map = {
            80: "HTTP",
            443: "HTTPS",
            53: "DNS",
            22: "SSH",
            21: "FTP",
            25: "SMTP"
        }
        return port_map.get(port, "Unknown")

    def _guess_app(self, port, sni, user_agent):
        if user_agent:
            agent = user_agent.lower()
            if "chrome" in agent: return "Google Chrome"
            if "firefox" in agent: return "Mozilla Firefox"
            if "safari" in agent and "chrome" not in agent: return "Apple Safari"
            if "curl" in agent: return "cURL"
            if "postman" in agent: return "Postman"
            return user_agent[:30] + "..." # return prefix of user agent
            
        if sni:
            sni_lower = sni.lower()
            if "google" in sni_lower: return "Google Services"
            if "facebook" in sni_lower or "whatsapp" in sni_lower: return "Meta Services"
            if "netflix" in sni_lower: return "Netflix"
            if "spotify" in sni_lower: return "Spotify"
            if "apple" in sni_lower or "icloud" in sni_lower: return "Apple Services"
            return sni # Return the SNI as the app name itself for clarity
            
        return "Unknown"
        
    def print_flows(self, limit=10):
        print(f"\n--- Recent Flows (showing last {limit}) ---")
        for f in self.flows[-limit:]:
            src_str = f'Src: {f.get("src_ip")}:{f.get("src_port")}'
            dst_str = f'Dst: {f.get("dst_ip")}:{f.get("dst_port")}'
            proto = f.get("protocol")
            service = f.get("service_name")
            src_app = f.get("src_app_name")
            dst_app = f.get("dst_app_name")
            sni = f.get("tls_sni")
            payload = f.get("payload_preview")
            
            line = f"{src_str} (App: {src_app}) | {dst_str} (App: {dst_app}) | Transport: {proto} | AppLayer: {service}"
            if sni: line += f" | TLS SNI: {sni}"
            if payload: line += f" | Payload: {payload}"
            print(line)
