from abc import ABC, abstractmethod

class PacketObserver(ABC):
    """
    Observer interface for processing packet data asynchronously or decoupled.
    """
    @abstractmethod
    def on_packet_parsed(self, packet_data: dict):
        pass


class Observable(ABC):
    """
    Subject interface to manage observers.
    """
    def __init__(self):
        self._observers = []

    def attach(self, observer: PacketObserver):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: PacketObserver):
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self, packet_data: dict):
        for observer in self._observers:
            observer.on_packet_parsed(packet_data)
