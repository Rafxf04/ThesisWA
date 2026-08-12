from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import numpy as np
from src.db.models import ImageLabel

class LabelingStrategy(ABC):
    """
    Strategy Pattern: Interfaccia comune per le strategie di etichettatura.
    Permette di variare gli algoritmi di classificazione senza alterare il Processor.
    """
    @abstractmethod
    def assign_label(self, image_path: str, labels: List[str], scores: np.ndarray) -> Optional[ImageLabel]:
        """
        Scopo: Assegna un'etichetta a un'immagine basata sui punteggi calcolati dal modello.

        Parametri:
        - image_path (str): Il percorso dell'immagine.
        - labels (List[str]): La lista delle etichette disponibili.
        - scores (np.ndarray): Array dei punteggi di similarità.

        Valore di ritorno:
        - Optional[ImageLabel]: L'oggetto ImageLabel risultante, oppure None.

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        pass

class ThresholdFallbackStrategy(LabelingStrategy):
    """
    Strategy Pattern: Implementazione concreta che assegna l'etichetta con il punteggio più alto.
    Se il punteggio è sotto una certa soglia, l'immagine viene marcata come 'is_partial'.
    """
    def __init__(self, threshold: float = 0.85):
        """
        Scopo: Inizializza la strategia con una soglia specifica.

        Parametri:
        - threshold (float): La soglia minima di confidenza per un match diretto.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        self.threshold = threshold

    def assign_label(self, image_path: str, labels: List[str], scores: np.ndarray) -> Optional[ImageLabel]:
        """
        Scopo: Valuta i punteggi e assegna la migliore etichetta; segnala se la confidenza è bassa.

        Parametri:
        - image_path (str): Il percorso dell'immagine da etichettare.
        - labels (List[str]): Lista delle etichette candidate.
        - scores (np.ndarray): Punteggi corrispondenti alle etichette.

        Valore di ritorno:
        - Optional[ImageLabel]: L'etichetta assegnata con l'informazione se è un match parziale.

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        if len(labels) == 0 or len(scores) == 0:
            return None
            
        best_idx = np.argmax(scores)
        best_score = float(scores[best_idx])
        best_label = labels[best_idx]
        
        is_partial = best_score < self.threshold
        
        return ImageLabel(
            image_path=image_path,
            label=best_label,
            score=best_score,
            is_partial=is_partial
        )
