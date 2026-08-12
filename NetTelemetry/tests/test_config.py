import unittest
from src.config import ConfigManager

class TestConfigManager(unittest.TestCase):
    def test_singleton_instance(self):
        """
        Scopo: Verifica che ConfigManager sia un vero Singleton (le istanze create condividono lo stesso riferimento).

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        c1 = ConfigManager()
        c2 = ConfigManager()
        self.assertIs(c1, c2)

    def test_get_and_set(self):
        """
        Scopo: Controlla che getter e setter di ConfigManager funzionino correttamente ed il default fallback agisca in assenza della chiave.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        c = ConfigManager()
        c.set("custom_setting", "test_value")
        self.assertEqual(c.get("custom_setting"), "test_value")
        self.assertEqual(c.get("non_existent", "default_val"), "default_val")

if __name__ == "__main__":
    unittest.main()
