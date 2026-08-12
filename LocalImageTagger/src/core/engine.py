import threading
from typing import List, Tuple
import numpy as np
import torch
from transformers import AutoProcessor
from optimum.intel.openvino import OVModelForZeroShotImageClassification
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ModelEngine:
    """
    Singleton Pattern: Motore di inferenza AI per l'elaborazione delle immagini tramite modello OpenVINO.
    Garantisce che il modello venga caricato in memoria una sola volta, ottimizzando l'uso delle risorse CPU.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelEngine, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_id: str = "openai/clip-vit-base-patch32"):
        """
        Scopo: Inizializza il motore del modello se non è già stato fatto.

        Parametri:
        - model_id (str): Identificativo del modello pre-addestrato da caricare.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        if not hasattr(self, 'initialized'):
            self.model_id = model_id
            self.processor = None
            self.model = None
            self.initialized = True
            self._load_model()

    def _load_model(self):
        """
        Scopo: Carica ed esporta in OpenVINO il modello AI per l'esecuzione ottimizzata su CPU.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista (errori di caricamento vengono gestiti dalla libreria sottostante).
        """
        logger.info(f"Caricamento del modello {self.model_id} via OpenVINO in corso...")
        self.processor = AutoProcessor.from_pretrained(self.model_id)
        self.model = OVModelForZeroShotImageClassification.from_pretrained(
            self.model_id, 
            export=True, 
            compile=True
        )
        logger.info("Modello caricato e compilato per CPU con successo.")

    def get_scores_and_embeddings(self, images: List, labels: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Scopo: Calcola i punteggi di affinità e gli embedding vettoriali per un batch di immagini rispetto a una lista di etichette.

        Parametri:
        - images (List): Lista di immagini (PIL.Image o array numpy).
        - labels (List[str]): Lista di testi/etichette da confrontare con le immagini.

        Valore di ritorno:
        - Tuple[np.ndarray, np.ndarray]: Tupla contenente la matrice delle probabilità (punteggi) e la matrice degli embedding vettoriali.

        Eccezioni:
        - AttributeError: Se il modello non restituisce gli embedding delle immagini.
        """
        inputs = self.processor(text=labels, images=images, return_tensors="pt", padding=True)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        logits_per_image = outputs.logits_per_image 
        probs = logits_per_image.softmax(dim=1).numpy()
        
        if hasattr(outputs, "image_embeds") and outputs.image_embeds is not None:
            embeds = outputs.image_embeds.numpy()
        else:
            raise AttributeError("Il modello OpenVINO non restituisce image_embeds.")
            
        norms = np.linalg.norm(embeds, axis=1, keepdims=True)
        embeds = embeds / (norms + 1e-9)
        
        return probs, embeds

    def get_image_embeddings(self, images: List) -> np.ndarray:
        """
        Scopo: Calcola esclusivamente gli embedding vettoriali per un batch di immagini, usando un testo fittizio.

        Parametri:
        - images (List): Lista di immagini.

        Valore di ritorno:
        - np.ndarray: Matrice contenente gli embedding normalizzati L2.

        Eccezioni:
        - AttributeError: Se il modello non restituisce gli embedding.
        """
        dummy_text = ["dummy"]
        inputs = self.processor(text=dummy_text, images=images, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        if hasattr(outputs, "image_embeds") and outputs.image_embeds is not None:
            embeds = outputs.image_embeds.numpy()
        else:
            raise AttributeError("Il modello OpenVINO non restituisce image_embeds.")
            
        norms = np.linalg.norm(embeds, axis=1, keepdims=True)
        return embeds / (norms + 1e-9)
