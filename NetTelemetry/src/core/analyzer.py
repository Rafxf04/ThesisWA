import pyshark
from src.patterns.observer import Observable
from src.core.strategy import TLSStrategy, HTTPStrategy, DNSStrategy, PayloadStrategy, ICMPStrategy, DHCPStrategy, NTPStrategy, QUICStrategy, SSDPStrategy, ARPStrategy

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
            ICMPStrategy(),
            DHCPStrategy(),
            NTPStrategy(),
            QUICStrategy(),
            SSDPStrategy(),
            ARPStrategy(),
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
            
        import time
        start_time = time.time()
        try:
            capture = pyshark.FileCapture(self.pcap_file, keep_packets=False)
            count = 0
            last_report_time = start_time
            last_report_count = 0

            for packet in capture:
                count += 1
                now = time.time()
                # Report every 1000 packets or every 2 seconds
                if count % 1000 == 0 or (now - last_report_time) >= 2.0:
                    elapsed = now - start_time
                    interval_elapsed = max(now - last_report_time, 0.001)
                    speed = (count - last_report_count) / interval_elapsed
                    mins, secs = divmod(int(elapsed), 60)
                    time_str = f"{mins:02d}:{secs:02d}"
                    print(f"[Progress] {count:,} packets processed | Speed: {speed:,.1f} pkts/s | Time: {time_str}", flush=True)
                    last_report_time = now
                    last_report_count = count

                self._process_packet(packet)

            capture.close()
            total_time = max(time.time() - start_time, 0.001)
            avg_speed = count / total_time
            mins, secs = divmod(int(total_time), 60)
            print(f"\n[Complete] Analysis finished! Total: {count:,} packets in {mins:02d}:{secs:02d} (Avg Speed: {avg_speed:,.1f} pkts/s)\n", flush=True)
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
            "timestamp": packet.sniff_timestamp,
            "highest_layer": packet.highest_layer,
            "length": int(packet.length),
            "src_ip": None,
            "dst_ip": None,
            "src_port": None,
            "dst_port": None,
            "mac_src": None,
            "mac_dst": None,
            "protocol": getattr(packet, 'transport_layer', None) or getattr(packet, 'highest_layer', 'Unknown')
        }

        # Ethernet layer (MAC addresses)
        if hasattr(packet, 'eth'):
            packet_data["mac_src"] = packet.eth.src
            packet_data["mac_dst"] = packet.eth.dst

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
