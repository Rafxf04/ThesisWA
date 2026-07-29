from questdb.ingress import Sender, IngressError, TimestampNanos
from src.config.manager import ConfigManager
import time

class QuestDBRepository:
    """
    Repository pattern to handle data insertion to QuestDB via InfluxDB Line Protocol.
    """
    def __init__(self, batch_size: int = 50):
        self.host = ConfigManager().get("questdb_host", "127.0.0.1")
        self.port = ConfigManager().get("questdb_ilp_port", 9009)
        self.sender = None
        self.connected = False
        self.batch_size = batch_size
        self.pending_count = 0

    def connect(self):
        try:
            # We connect using the ILP (Influx Line Protocol) TCP port 9009
            self.sender = Sender('tcp', self.host, self.port, auto_flush=True)
            self.sender.establish()
            self.connected = True
            print(f"Connected to QuestDB at {self.host}:{self.port} (ILP TCP)")
        except Exception as e:
            print(f"QuestDB connection offline/unavailable at {self.host}:{self.port} ({e})")
            self.connected = False

    def insert_packet(self, flow_data: dict):
        if not self.connected or not self.sender:
            return
            
        try:
            # Timestamp extraction: use PCAP packet sniff timestamp if available (in float seconds)
            pkt_ts = flow_data.get('timestamp')
            if pkt_ts is not None:
                at_ns = int(float(pkt_ts) * 1_000_000_000)
            else:
                at_ns = time.time_ns()

            # Construct row
            self.sender.row(
                'network_traffic',
                symbols={
                    'protocol': str(flow_data.get('protocol') or 'Unknown'),
                    'service_name': str(flow_data.get('service_name') or 'Unknown'),
                    'src_ip': str(flow_data.get('src_ip') or ''),
                    'dst_ip': str(flow_data.get('dst_ip') or ''),
                    'src_app_name': str(flow_data.get('src_app_name') or 'Unknown'),
                    'dst_app_name': str(flow_data.get('dst_app_name') or 'Unknown'),
                    'geo_country': str(flow_data.get('geo_country') or 'Unknown'),
                },
                columns={
                    'src_port': int(flow_data.get('src_port') or 0),
                    'dst_port': int(flow_data.get('dst_port') or 0),
                    'length': int(flow_data.get('length') or 0),
                    'tls_sni': str(flow_data.get('tls_sni') or ''),
                    'payload_len': int(flow_data.get('payload_len') or 0)
                },
                at=TimestampNanos(at_ns)
            )
            self.pending_count += 1
            if self.pending_count >= self.batch_size:
                self.flush()
        except IngressError as e:
            print(f"QuestDB Ingress Error: {e}")
        except Exception as e:
            print(f"Error inserting packet to QuestDB: {e}")

    def flush(self):
        if self.sender and self.connected and self.pending_count > 0:
            try:
                self.sender.flush()
                self.pending_count = 0
            except IngressError as e:
                print(f"QuestDB Flush Error: {e}")
            except Exception as e:
                print(f"QuestDB Flush Failed: {e}")

    def close(self):
        if self.sender and self.connected:
            try:
                self.flush()
                self.sender.close()
            except Exception as e:
                print(f"Error closing QuestDB connection: {e}")
            finally:
                self.connected = False
