from questdb.ingress import Sender, IngressError, TimestampNanos
from src.config import ConfigManager
import time

class QuestDBRepository:
    """
    Repository pattern to handle data insertion to QuestDB via InfluxDB Line Protocol.
    """
    def __init__(self, table_name: str = "network_traffic", batch_size: int = 500):
        self.table_name = table_name
        self.host = ConfigManager().get("questdb_host", "127.0.0.1")
        self.port = ConfigManager().get("questdb_http_port", 9000)
        self.sender = None
        self.connected = False
        self.batch_size = batch_size
        self.pending_count = 0
        self.last_reconnect_attempt = 0

    def connect(self):
        if self.connected and self.sender is not None:
            return
        self.last_reconnect_attempt = time.time()
        try:
            self.sender = Sender('http', self.host, self.port)
            self.sender.establish()
            self.connected = True
            print(f"Connected to QuestDB at {self.host}:{self.port} (ILP HTTP)")
        except Exception as e:
            self.connected = False
            print(f"QuestDB connection offline/unavailable at {self.host}:{self.port} ({e})")

    def insert_packet(self, flow_data: dict):
        if not self.connected or self.sender is None:
            now = time.time()
            if now - self.last_reconnect_attempt > 5.0:
                self.connect()
            if not self.connected or self.sender is None:
                return
            
        try:
            # Timestamp extraction: preserve full nanosecond precision without float conversion
            pkt_ts = flow_data.get('timestamp')
            if pkt_ts is not None:
                if isinstance(pkt_ts, str):
                    parts = pkt_ts.split('.')
                    sec = int(parts[0])
                    nsec = int(parts[1][:9].ljust(9, '0')) if len(parts) > 1 else 0
                    at_ns = sec * 1_000_000_000 + nsec
                else:
                    at_ns = int(float(pkt_ts) * 1_000_000_000)
            else:
                at_ns = time.time_ns()

            # Construct row
            self.sender.row(
                self.table_name,
                symbols={
                    'protocol': str(flow_data.get('protocol') or 'Unknown'),
                    'service_name': str(flow_data.get('service_name') or 'Unknown'),
                    'src_ip': str(flow_data.get('src_ip') or 'Unknown'),
                    'dst_ip': str(flow_data.get('dst_ip') or 'Unknown'),
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
            print(f"QuestDB Ingress Error: {type(e)} - {e}")
        except Exception as e:
            print(f"Error inserting packet to QuestDB: {type(e)} - {e}")

    def flush(self):
        if self.sender is not None and self.connected:
            try:
                self.sender.flush()
                self.pending_count = 0
            except Exception as e:
                print(f"QuestDB Flush Warning: {type(e)} - {e}")

    def close(self):
        if self.sender is not None and self.connected:
            try:
                self.flush()
                self.sender.close()
            except Exception as e:
                print(f"Error closing QuestDB connection: {e}")
            finally:
                self.connected = False
