from abc import ABC, abstractmethod
import pyshark

class ProtocolStrategy(ABC):
    """
    Strategy interface for parsing specific layers of a packet.
    """
    @abstractmethod
    def can_handle(self, packet) -> bool:
        pass
        
    @abstractmethod
    def extract_data(self, packet) -> dict:
        """
        Extracts relevant information from the packet layer.
        Returns a dictionary with extracted features.
        """
        pass

class TLSStrategy(ProtocolStrategy):
    def can_handle(self, packet):
        return 'TLS' in packet
        
    def extract_data(self, packet):
        data = {"tls_sni": None, "tls_version": None}
        try:
            # Extract Server Name Indication (SNI) if present
            if hasattr(packet.tls, 'handshake_extensions_server_name'):
                data["tls_sni"] = packet.tls.handshake_extensions_server_name
            if hasattr(packet.tls, 'record_version'):
                data["tls_version"] = packet.tls.record_version
        except AttributeError:
            pass
        return data

class HTTPStrategy(ProtocolStrategy):
    def can_handle(self, packet):
        return 'HTTP' in packet
        
    def extract_data(self, packet):
        data = {"http_host": None, "http_uri": None, "http_method": None, "http_user_agent": None}
        try:
            if hasattr(packet.http, 'host'):
                data["http_host"] = packet.http.host
            if hasattr(packet.http, 'request_uri'):
                data["http_uri"] = packet.http.request_uri
            if hasattr(packet.http, 'request_method'):
                data["http_method"] = packet.http.request_method
            if hasattr(packet.http, 'user_agent'):
                data["http_user_agent"] = packet.http.user_agent
        except AttributeError:
            pass
        return data

class DNSStrategy(ProtocolStrategy):
    def can_handle(self, packet):
        return 'DNS' in packet
        
    def extract_data(self, packet):
        data = {"dns_query": None}
        try:
            if hasattr(packet.dns, 'qry_name'):
                data["dns_query"] = packet.dns.qry_name
        except AttributeError:
            pass
        return data

class PayloadStrategy(ProtocolStrategy):
    """Extracts raw payload if available and unencrypted (mostly UDP/TCP)"""
    def can_handle(self, packet):
        return hasattr(packet, 'data') or hasattr(packet, 'tcp')
        
    def extract_data(self, packet):
        data = {"payload_len": 0, "payload_preview": None}
        try:
            if hasattr(packet, 'tcp') and hasattr(packet.tcp, 'payload'):
                # Extract ascii preview of the payload
                raw = packet.tcp.payload.replace(":", "")
                data["payload_len"] = len(raw) // 2
                try:
                    data["payload_preview"] = bytes.fromhex(raw).decode('utf-8', errors='ignore')[:50]
                except Exception:
                    pass
            elif hasattr(packet, 'data') and hasattr(packet.data, 'data'):
                raw = packet.data.data.replace(":", "")
                data["payload_len"] = len(raw) // 2
                try:
                    data["payload_preview"] = bytes.fromhex(raw).decode('utf-8', errors='ignore')[:50]
                except Exception:
                    pass
        except AttributeError:
            pass
        return data

