from dataclasses import dataclass
from typing import Optional

@dataclass
class ImageLabel:
    """
    Scopo: DTO (Data Transfer Object) che rappresenta le informazioni di etichettatura per una singola immagine.
    
    Attributi:
    - image_path: Percorso locale dell'immagine.
    - label: Etichetta predetta o assegnata.
    - score: Affidabilità della predizione (0.0 - 1.0).
    - is_partial: True se lo score è al di sotto della soglia di sicurezza.
    - user_verified: True se l'etichetta è stata validata dall'utente.
    - image_data: Dati binari opzionali (thumbnail dell'immagine).
    - embedding: Vettore embedding generato dal modello AI per Ricerca per Similarità (Few-Shot).
    - id: Identificativo primario a DB.
    """
    image_path: str
    label: str
    score: float
    is_partial: bool
    user_verified: bool = False
    image_data: Optional[bytes] = None
    embedding: Optional[bytes] = None
    id: Optional[int] = None
