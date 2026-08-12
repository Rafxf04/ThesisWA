import unittest
from src.patterns.trackers import StatsTracker, FlowTracker

class TestTrackers(unittest.TestCase):
    def test_stats_tracker(self):
        """
        Scopo: Verifica che StatsTracker accumuli i dati statistici correttamente aggregati per protocollo.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        tracker = StatsTracker()
        tracker.on_packet_parsed({"protocol": "TCP", "length": 100})
        tracker.on_packet_parsed({"protocol": "TCP", "length": 200})
        tracker.on_packet_parsed({"protocol": "UDP", "length": 50})

        self.assertEqual(tracker.total_packets, 3)
        self.assertEqual(tracker.protocol_counts["TCP"], 2)
        self.assertEqual(tracker.protocol_counts["UDP"], 1)
        self.assertEqual(tracker.protocol_bytes["TCP"], 300)

    def test_flow_tracker_app_guessing(self):
        """
        Scopo: Controlla che le logiche DPI e la deduzione dei protocolli di base di FlowTracker siano affidabili.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        flow_tracker = FlowTracker()
        self.assertEqual(flow_tracker._guess_service(80), "HTTP")
        self.assertEqual(flow_tracker._guess_service(443), "HTTPS")
        self.assertEqual(flow_tracker._guess_service(53), "DNS")

        # Test dell'identify_application simulato
        # Poichè _identify_application gestisce parametri come (port, sni, user_agent, http_host)
        res_chrome, _ = flow_tracker._identify_application(80, None, "Mozilla/5.0 Chrome/114.0", None)
        self.assertEqual(res_chrome, "Google Chrome")
        
        res_meta, _ = flow_tracker._identify_application(443, "whatsapp.net", None, None)
        self.assertEqual(res_meta, "WhatsApp")

if __name__ == "__main__":
    unittest.main()
