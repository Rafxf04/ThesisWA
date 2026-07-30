import argparse
import sys
import os

# Ensure src module can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core import PcapAnalyzer
from src.patterns import StatsTracker, FlowTracker
from src.enrichment import IpApiEnrichment, CacheProxy
from src.storage import QuestDBRepository

def main():
    parser = argparse.ArgumentParser(description="NetTelemetry - PCAP Analytics & Storage Engine")
    parser.add_argument("-pcap", required=True, help="Path to the PCAP file")
    parser.add_argument("--table", default="network_traffic", help="QuestDB table name")
    parser.add_argument("--no-db", action="store_true", help="Disable QuestDB export")
    parser.add_argument("--no-enrich", action="store_true", help="Disable IP-API enrichment")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pcap):
        print(f"Error: PCAP file not found: {args.pcap}")
        sys.exit(1)
        
    # 1. Setup Enrichment (Proxy Pattern)
    enrich_service = None
    if not args.no_enrich:
        print("Initializing IP-API Enrichment with Cache...")
        enrich_service = CacheProxy(IpApiEnrichment())

    # 2. Setup Storage (Repository Pattern)
    db_repo = None
    if not args.no_db:
        print(f"Initializing QuestDB connection (Table: {args.table})...")
        db_repo = QuestDBRepository(table_name=args.table)
        db_repo.connect()

    # 3. Setup Trackers (Observer Pattern)
    stats_tracker = StatsTracker()
    flow_tracker = FlowTracker(enrichment_service=enrich_service, db_repo=db_repo)

    # 4. Setup Analyzer (Facade Pattern)
    analyzer = PcapAnalyzer(args.pcap)
    
    # Wire Observers
    analyzer.attach(stats_tracker)
    analyzer.attach(flow_tracker)

    # 5. Run analysis
    try:
        analyzer.analyze()
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
    finally:
        if db_repo:
            db_repo.close()

        # Print results
        stats_tracker.print_stats()
        flow_tracker.print_flows(limit=20)
        print("Done.")

if __name__ == "__main__":
    main()
