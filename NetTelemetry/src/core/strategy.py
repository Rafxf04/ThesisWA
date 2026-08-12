from abc import ABC, abstractmethod
import pyshark

class ProtocolStrategy(ABC):
    """
    Strategy Pattern: Interfaccia per il parsing di specifici livelli di un pacchetto di rete.
    """
    @abstractmethod
    def can_handle(self, packet) -> bool:
        """
        Scopo: Determina se questa strategia può gestire il pacchetto fornito.

        Parametri:
        - packet: Il pacchetto da analizzare.

        Valore di ritorno:
        - bool: True se la strategia è applicabile, False altrimenti.

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        pass
        
    @abstractmethod
    def extract_data(self, packet) -> dict:
        """
        Scopo: Estrae le informazioni rilevanti dal pacchetto specifico per questo protocollo.

        Parametri:
        - packet: Il pacchetto da cui estrarre i dati.

        Valore di ritorno:
        - dict: Dizionario con le feature estratte.

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        pass

class TLSStrategy(ProtocolStrategy):
    def can_handle(self, packet):
        return 'TLS' in packet
        
    def extract_data(self, packet):
        data = {
            "tls_sni": None, 
            "tls_version": None,
            "tls_ciphersuites": None,
            "tls_certificate": None
        }
        try:
            # Extract Server Name Indication (SNI) if present
            if hasattr(packet.tls, 'handshake_extensions_server_name'):
                data["tls_sni"] = packet.tls.handshake_extensions_server_name
            if hasattr(packet.tls, 'record_version'):
                ver = str(packet.tls.record_version).lower().strip()
                version_map = {
                    "0x0304": "TLS 1.3",
                    "0x0303": "TLS 1.2",
                    "0x0302": "TLS 1.1",
                    "0x0301": "TLS 1.0",
                    "0x0300": "SSL 3.0",
                    "0x0002": "SSL 2.0"
                }
                data["tls_version"] = version_map.get(ver, ver)
                
            # Extract Ciphersuites (Supported by client or chosen by server)
            if hasattr(packet.tls, 'handshake_ciphersuite'):
                data["tls_ciphersuites"] = packet.tls.handshake_ciphersuite
            elif hasattr(packet.tls, 'handshake_ciphersuites'):
                # In Client Hello, it's a list/string of supported ciphers. We might truncate it if too long.
                ciphers = str(packet.tls.handshake_ciphersuites)
                data["tls_ciphersuites"] = ciphers[:100] + "..." if len(ciphers) > 100 else ciphers

            # Extract Certificate information (e.g., DNS name or Subject from x509)
            if hasattr(packet.tls, 'x509ce_dnsname'):
                data["tls_certificate"] = packet.tls.x509ce_dnsname
            elif hasattr(packet.tls, 'x509sat_utf8string'):
                data["tls_certificate"] = packet.tls.x509sat_utf8string
                
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
            raw = None
            if hasattr(packet, 'tcp') and hasattr(packet.tcp, 'payload'):
                raw = packet.tcp.payload.replace(":", "")
            elif hasattr(packet, 'data') and hasattr(packet.data, 'data'):
                raw = packet.data.data.replace(":", "")
                
            if raw:
                data["payload_len"] = len(raw) // 2
                try:
                    decoded = bytes.fromhex(raw).decode('utf-8', errors='ignore')[:50]
                    printable = "".join(c if 32 <= ord(c) <= 126 else "." for c in decoded)
                    if printable.strip("."):
                        data["payload_preview"] = printable
                except Exception:
                    pass
        except AttributeError:
            pass
        return data

class ICMPStrategy(ProtocolStrategy):
    def can_handle(self, packet):
        return 'ICMP' in packet or 'ICMPV6' in packet
        
    def extract_data(self, packet):
        data = {"icmp_type": None, "icmp_code": None}
        try:
            layer = packet.icmpv6 if hasattr(packet, 'icmpv6') else packet.icmp
            if hasattr(layer, 'type'):
                data["icmp_type"] = layer.type
            if hasattr(layer, 'code'):
                data["icmp_code"] = layer.code
        except AttributeError:
            pass
        return data

class DHCPStrategy(ProtocolStrategy):
    def can_handle(self, packet):
        return 'BOOTP' in packet or 'DHCP' in packet
        
    def extract_data(self, packet):
        data = {"dhcp_hostname": None, "dhcp_mac": None}
        try:
            # Pyshark usually parses DHCP as BOOTP
            layer = packet.dhcp if hasattr(packet, 'dhcp') else packet.bootp
            if hasattr(layer, 'option_hostname'):
                data["dhcp_hostname"] = layer.option_hostname
            if hasattr(layer, 'hw_mac_addr'):
                data["dhcp_mac"] = layer.hw_mac_addr
        except AttributeError:
            pass
        return data

class NTPStrategy(ProtocolStrategy):
    def can_handle(self, packet):
        return 'NTP' in packet
        
    def extract_data(self, packet):
        data = {"ntp_flags": None}
        try:
            if hasattr(packet.ntp, 'flags'):
                data["ntp_flags"] = packet.ntp.flags
        except AttributeError:
            pass
        return data

class QUICStrategy(ProtocolStrategy):
    def can_handle(self, packet):
        return 'QUIC' in packet
        
    def extract_data(self, packet):
        data = {"quic_dcid": None, "quic_scid": None}
        try:
            if hasattr(packet.quic, 'dcid'):
                data["quic_dcid"] = packet.quic.dcid
            if hasattr(packet.quic, 'scid'):
                data["quic_scid"] = packet.quic.scid
        except AttributeError:
            pass
        return data

class SSDPStrategy(ProtocolStrategy):
    def can_handle(self, packet):
        return 'SSDP' in packet
        
    def extract_data(self, packet):
        data = {"ssdp_st": None, "ssdp_location": None}
        try:
            if hasattr(packet.ssdp, 'st'):
                data["ssdp_st"] = packet.ssdp.st
            if hasattr(packet.ssdp, 'location'):
                data["ssdp_location"] = packet.ssdp.location
        except AttributeError:
            pass
        return data

class ARPStrategy(ProtocolStrategy):
    def can_handle(self, packet):
        return 'ARP' in packet
        
    def extract_data(self, packet):
        data = {"arp_opcode": None, "arp_src_mac": None, "arp_dst_mac": None}
        try:
            if hasattr(packet.arp, 'opcode'):
                data["arp_opcode"] = packet.arp.opcode
            if hasattr(packet.arp, 'src_hw_mac'):
                data["arp_src_mac"] = packet.arp.src_hw_mac
            if hasattr(packet.arp, 'dst_hw_mac'):
                data["arp_dst_mac"] = packet.arp.dst_hw_mac
        except AttributeError:
            pass
        return data
