import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core import PcapAnalyzer
from src.patterns import StatsTracker, FlowTracker
from src.enrichment import IpApiEnrichment, CacheProxy
from src.storage import QuestDBRepository

def main():
    """
    Scopo: Punto di ingresso principale dell'applicazione NetTelemetry. Avvia l'analisi del traffico di rete da un file PCAP.

    Parametri:
    - Nessuno (i parametri vengono presi da riga di comando).

    Valore di ritorno:
    - Nessuno

    Eccezioni:
    - SystemExit: Se il file PCAP non esiste o il database QuestDB non è raggiungibile.
    """
    parser = argparse.ArgumentParser(description="NetTelemetry - PCAP Analytics & Storage Engine")
    parser.add_argument("-pcap", required=True, help="Path to the PCAP file")
    parser.add_argument("--table", default="network_traffic", help="QuestDB table name")
    parser.add_argument("--no-db", action="store_true", help="Disable QuestDB export")
    parser.add_argument("--no-enrich", action="store_true", help="Disable IP-API enrichment")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pcap):
        print(f"Error: PCAP file not found: {args.pcap}")
        sys.exit(1)
        
    enrich_service = None
    if not args.no_enrich:
        print("Initializing IP-API Enrichment with Cache...")
        enrich_service = CacheProxy(IpApiEnrichment())

    db_repo = None
    if not args.no_db:
        print(f"Initializing QuestDB connection (Table: {args.table})...")
        db_repo = QuestDBRepository(table_name=args.table)
        success = db_repo.connect()
        if not success:
            print("\n[FATAL ERROR] QuestDB is offline or unreachable!")
            print("Please start your QuestDB Docker container (port 9000).")
            print("To run the analysis without saving to the database, use the --no-db flag.")
            sys.exit(1)

    stats_tracker = StatsTracker()
    flow_tracker = FlowTracker(enrichment_service=enrich_service, db_repo=db_repo)

    analyzer = PcapAnalyzer(args.pcap)
    
    analyzer.attach(stats_tracker)
    analyzer.attach(flow_tracker)

    try:
        analyzer.analyze()
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
    finally:
        if db_repo:
            db_repo.close()
        
        if enrich_service and hasattr(enrich_service, 'flush'):
            enrich_service.flush()

        stats_tracker.print_stats()
        flow_tracker.print_flows(limit=20)
        print("Done.")

if __name__ == "__main__":
    main()
