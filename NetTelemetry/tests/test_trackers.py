import unittest
from src.patterns.trackers import StatsTracker, FlowTracker

class TestTrackers(unittest.TestCase):
    def test_stats_tracker(self):
        tracker = StatsTracker()
        tracker.on_packet_parsed({"protocol": "TCP", "length": 100})
        tracker.on_packet_parsed({"protocol": "TCP", "length": 200})
        tracker.on_packet_parsed({"protocol": "UDP", "length": 50})

        self.assertEqual(tracker.total_packets, 3)
        self.assertEqual(tracker.protocol_counts["TCP"], 2)
        self.assertEqual(tracker.protocol_counts["UDP"], 1)
        self.assertEqual(tracker.protocol_bytes["TCP"], 300)

    def test_flow_tracker_app_guessing(self):
        flow_tracker = FlowTracker()
        self.assertEqual(flow_tracker._guess_service(80), "HTTP")
        self.assertEqual(flow_tracker._guess_service(443), "HTTPS")
        self.assertEqual(flow_tracker._guess_service(53), "DNS")

        self.assertEqual(flow_tracker._guess_app(80, None, "Mozilla/5.0 Chrome/114.0"), "Google Chrome")
        self.assertEqual(flow_tracker._guess_app(443, "whatsapp.net", None), "Meta Services")

if __name__ == "__main__":
    unittest.main()
