from questdb.ingress import Sender, IngressError, TimestampNanos
from src.config import ConfigManager
import time

class QuestDBRepository:
    """
    Repository Pattern: Isola la logica di accesso e scrittura sul database QuestDB
    (tramite InfluxDB Line Protocol) dal resto dell'applicazione.
    """
    def __init__(self, table_name: str = "network_traffic", batch_size: int = 500):
        """
        Scopo: Inizializza il repository con le configurazioni di base.

        Parametri:
        - table_name (str): Il nome della tabella di destinazione.
        - batch_size (int): Numero di record da accumulare prima del flush.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        self.table_name = table_name
        self.host = ConfigManager().get("questdb_host", "127.0.0.1")
        self.port = ConfigManager().get("questdb_http_port", 9000)
        self.sender = None
        self.connected = False
        self.batch_size = batch_size
        self.pending_count = 0
        self.last_reconnect_attempt = 0

    def connect(self) -> bool:
        """
        Scopo: Stabilisce o verifica la connessione verso QuestDB via ILP HTTP.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - bool: True se connesso con successo, False altrimenti.

        Eccezioni:
        - Le eccezioni di rete vengono intercettate e gestite stampando un log.
        """
        if self.connected and self.sender is not None:
            return True
        self.last_reconnect_attempt = time.time()
        try:
            self.sender = Sender('http', self.host, self.port)
            self.sender.establish()
            self.connected = True
            print(f"Connected to QuestDB at {self.host}:{self.port} (ILP HTTP)")
            return True
        except Exception as e:
            self.connected = False
            print(f"QuestDB connection offline/unavailable at {self.host}:{self.port} ({e})")
            return False

    def insert_packet(self, flow_data: dict):
        """
        Scopo: Inserisce un nuovo record nel database bufferizzandolo in batch. 
        Garantisce la precisione a nanosecondi per i timestamp temporali.

        Parametri:
        - flow_data (dict): I dati del pacchetto da registrare.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Le eccezioni di inserimento (es. IngressError) vengono catturate e loggate.
        """
        if not self.connected or self.sender is None:
            now = time.time()
            if now - self.last_reconnect_attempt > 5.0:
                self.connect()
            if not self.connected or self.sender is None:
                return
            
        try:
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

            self.sender.row(
                self.table_name,
                symbols={
                    'protocol': str(flow_data.get('protocol') or 'Unknown'),
                    'service_name': str(flow_data.get('service_name') or 'Unknown'),
                    'src_ip': str(flow_data.get('src_ip') or 'Unknown'),
                    'dst_ip': str(flow_data.get('dst_ip') or 'Unknown'),
                    'src_app_name': str(flow_data.get('src_app_name') or 'Unknown'),
                    'src_category': str(flow_data.get('src_category') or 'Unknown'),
                    'dst_app_name': str(flow_data.get('dst_app_name') or 'Unknown'),
                    'dst_category': str(flow_data.get('dst_category') or 'Unknown'),
                    'geo_country': str(flow_data.get('geo_country') or 'Unknown'),
                    'mac_src': str(flow_data.get('mac_src') or 'Unknown'),
                    'mac_dst': str(flow_data.get('mac_dst') or 'Unknown'),
                },
                columns={
                    'src_port': int(flow_data.get('src_port') or 0),
                    'dst_port': int(flow_data.get('dst_port') or 0),
                    'length': int(flow_data.get('length') or 0),
                    'tls_sni': str(flow_data.get('tls_sni') or ''),
                    'tls_version': str(flow_data.get('tls_version') or ''),
                    'tls_ciphersuites': str(flow_data.get('tls_ciphersuites') or ''),
                    'tls_certificate': str(flow_data.get('tls_certificate') or ''),
                    'http_host': str(flow_data.get('http_host') or ''),
                    'http_method': str(flow_data.get('http_method') or ''),
                    'http_uri': str(flow_data.get('http_uri') or ''),
                    'http_user_agent': str(flow_data.get('http_user_agent') or ''),
                    'dns_query': str(flow_data.get('dns_query') or ''),
                    'payload_len': int(flow_data.get('payload_len') or 0),
                    'payload_preview': str(flow_data.get('payload_preview') or '')
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
        """
        Scopo: Svuota il buffer dei record in attesa, inviandoli tutti al database in una singola richiesta.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione propagata.
        """
        if self.sender is not None and self.connected:
            try:
                self.sender.flush()
                self.pending_count = 0
            except Exception as e:
                print(f"QuestDB Flush Warning: {type(e)} - {e}")

    def close(self):
        """
        Scopo: Svuota il buffer finale e chiude ordinatamente la connessione al database.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione propagata.
        """
        if self.sender is not None and self.connected:
            try:
                self.flush()
                self.sender.close()
            except Exception as e:
                print(f"Error closing QuestDB connection: {e}")
            finally:
                self.connected = False
