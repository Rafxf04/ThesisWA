import unittest
from src.config import ConfigManager

class TestConfigManager(unittest.TestCase):
    def test_singleton_instance(self):
        c1 = ConfigManager()
        c2 = ConfigManager()
        self.assertIs(c1, c2)

    def test_get_and_set(self):
        c = ConfigManager()
        c.set("custom_setting", "test_value")
        self.assertEqual(c.get("custom_setting"), "test_value")
        self.assertEqual(c.get("non_existent", "default_val"), "default_val")

if __name__ == "__main__":
    unittest.main()
