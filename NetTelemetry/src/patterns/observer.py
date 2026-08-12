from abc import ABC, abstractmethod

class PacketObserver(ABC):
    """
    Observer Pattern: Interfaccia per gli osservatori che si mettono in ascolto dei pacchetti parsati.
    """
    @abstractmethod
    def on_packet_parsed(self, packet_data: dict):
        """
        Scopo: Metodo chiamato dall'Observable ogni volta che un pacchetto viene decodificato.

        Parametri:
        - packet_data (dict): I dati estratti dal pacchetto.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        pass

class Observable(ABC):
    """
    Observer Pattern: Classe base per soggetti (Subject) che gestiscono la lista degli osservatori
    e li notificano dei cambiamenti di stato.
    """
    def __init__(self):
        self._observers = []

    def attach(self, observer: PacketObserver):
        """
        Scopo: Registra un nuovo osservatore per ricevere le notifiche.

        Parametri:
        - observer (PacketObserver): L'osservatore da registrare.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: PacketObserver):
        """
        Scopo: Rimuove un osservatore dalla lista, smettendo di notificargli gli eventi.

        Parametri:
        - observer (PacketObserver): L'osservatore da rimuovere.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self, packet_data: dict):
        """
        Scopo: Notifica tutti gli osservatori registrati inviando loro i dati del pacchetto.

        Parametri:
        - packet_data (dict): I dati del pacchetto da broadcastare.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        for observer in self._observers:
            observer.on_packet_parsed(packet_data)
