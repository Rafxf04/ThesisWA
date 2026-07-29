import pyshark
from src.patterns.observer import Observable
from src.core.strategy import TLSStrategy, HTTPStrategy, DNSStrategy, PayloadStrategy

class PcapAnalyzer(Observable):
    """
    Facade class that handles reading PCAP files and coordinating parsing strategies.
    Uses the Observer pattern to notify listeners (trackers) of parsed packets.
    """
    def __init__(self, pcap_file):
        super().__init__()
        self.pcap_file = pcap_file
        # Register available strategies
        self.strategies = [
            TLSStrategy(),
            HTTPStrategy(),
            DNSStrategy(),
            PayloadStrategy()
        ]

    def analyze(self):
        """
        Starts reading the PCAP file and processing each packet.
        """
        print(f"Starting analysis on {self.pcap_file}...")
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        try:
            capture = pyshark.FileCapture(self.pcap_file, keep_packets=False)
            for packet in capture:
                self._process_packet(packet)
            capture.close()
        except FileNotFoundError:
            print(f"Error: PCAP file not found: {self.pcap_file}")
        except Exception as e:
            print(f"Error during parsing: {e}")

    def _process_packet(self, packet):
        """
        Extracts basic flow info and applies strategies to get detailed data.
        """
        # Basic packet info
        packet_data = {
            "timestamp": float(packet.sniff_timestamp),
            "highest_layer": packet.highest_layer,
            "length": int(packet.length),
            "src_ip": None,
            "dst_ip": None,
            "src_port": None,
            "dst_port": None,
            "protocol": packet.transport_layer if hasattr(packet, 'transport_layer') else packet.highest_layer
        }

        # IP layer
        if hasattr(packet, 'ip'):
            packet_data["src_ip"] = packet.ip.src
            packet_data["dst_ip"] = packet.ip.dst
        elif hasattr(packet, 'ipv6'):
            packet_data["src_ip"] = packet.ipv6.src
            packet_data["dst_ip"] = packet.ipv6.dst

        # Transport layer
        if hasattr(packet, 'tcp'):
            packet_data["src_port"] = int(packet.tcp.srcport)
            packet_data["dst_port"] = int(packet.tcp.dstport)
        elif hasattr(packet, 'udp'):
            packet_data["src_port"] = int(packet.udp.srcport)
            packet_data["dst_port"] = int(packet.udp.dstport)

        # Apply Strategies to extract additional metadata (SNI, Host, Payload, etc.)
        for strategy in self.strategies:
            if strategy.can_handle(packet):
                extra_data = strategy.extract_data(packet)
                # Merge dictionaries
                packet_data.update(extra_data)

        # Notify Observers (Trackers)
        self.notify(packet_data)
