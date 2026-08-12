import os
import cv2
from typing import List
import io
from PIL import Image
import numpy as np
from src.core.engine import ModelEngine
from src.labeling.strategy import LabelingStrategy
from src.db.repository import LabelRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ImageBatchProcessor:
    def __init__(self, 
                 engine: ModelEngine, 
                 strategy: LabelingStrategy, 
                 repository: LabelRepository,
                 batch_size: int = 8):
        """
        Scopo: Inizializza il processore batch per elaborare iterativamente gruppi di immagini.

        Parametri:
        - engine (ModelEngine): Motore IA utilizzato per l'inferenza.
        - strategy (LabelingStrategy): Strategia per l'assegnazione delle etichette.
        - repository (LabelRepository): Classe per l'accesso e la memorizzazione sul database.
        - batch_size (int): Numero di immagini da processare contemporaneamente.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        self.engine = engine
        self.strategy = strategy
        self.repository = repository
        self.batch_size = batch_size

    def process_directory(self, directory: str, labels: List[dict]):
        """
        Scopo: Scansiona una directory ed esegue l'elaborazione batch su tutte le immagini trovate.

        Parametri:
        - directory (str): Percorso della cartella contenente le immagini.
        - labels (List[dict]): Lista delle etichette supportate per la classificazione.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        if not os.path.isdir(directory):
            logger.error(f"Directory not found: {directory}")
            return

        self.verified_memory = self.repository.get_verified_embeddings()
        if self.verified_memory:
            logger.info(f"Memoria Visiva caricata: {len(self.verified_memory)} immagini verificate.")
        else:
            logger.info("Nessuna Memoria Visiva precedente trovata.")

        valid_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
        image_paths = []
        for root, _, files in os.walk(directory):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in valid_extensions:
                    image_paths.append(os.path.join(root, file))
        
        total_images = len(image_paths)
        if total_images == 0:
            logger.info(f"Nessuna immagine trovata in {directory}")
            return
            
        logger.info(f"Trovate {total_images} immagini da elaborare.")

        for i in range(0, total_images, self.batch_size):
            batch_paths = image_paths[i:i + self.batch_size]
            self._process_batch(batch_paths, labels)
            
            logger.info(f"Processate {min(i + self.batch_size, total_images)}/{total_images} immagini.")

    def _process_batch(self, batch_paths: List[str], labels: List[dict]):
        """
        Scopo: Carica in memoria ed esegue l'inferenza AI su un singolo batch di immagini, memorizzandole.

        Parametri:
        - batch_paths (List[str]): Lista dei percorsi delle immagini del batch corrente.
        - labels (List[dict]): Lista delle etichette supportate.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista (errori individuali vengono loggati e bypassati).
        """
        images = []
        valid_paths = []
        
        for path in batch_paths:
            try:
                cv_img = cv2.imread(path)
                if cv_img is None:
                    continue
                cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(cv_img)
                
                images.append(pil_img)
                valid_paths.append(path)
            except Exception as e:
                logger.error(f"Errore caricamento {path}: {e}")
                
        if not images:
            return
            
        image_blobs = []
        for img in images:
            thumb = img.copy()
            thumb.thumbnail((1024, 1024))
            b = io.BytesIO()
            thumb.save(b, format="JPEG")
            image_blobs.append(b.getvalue())
            
        english_prompts = [f"a photo of a {l['prompt']}" for l in labels]
        save_names = [l['save_name'] for l in labels]
            
        scores_matrix, embeddings_matrix = self.engine.get_scores_and_embeddings(images, english_prompts)
        
        labels_to_save = []
        for idx, path in enumerate(valid_paths):
            scores = scores_matrix[idx]
            emb = embeddings_matrix[idx]
            
            memory_match = None
            if hasattr(self, 'verified_memory') and self.verified_memory:
                best_sim = -1
                best_label = None
                for mem in self.verified_memory:
                    mem_emb = np.frombuffer(mem.embedding, dtype=np.float32)
                    sim = np.dot(emb, mem_emb)
                    if sim > best_sim:
                        best_sim = sim
                        best_label = mem.label
                
                if best_sim > 0.90:
                    memory_match = best_label
                    
            if memory_match:
                from src.db.models import ImageLabel
                image_label = ImageLabel(
                    image_path=path,
                    label=memory_match,
                    score=1.0,
                    is_partial=False
                )
            else:
                image_label = self.strategy.assign_label(path, save_names, scores)
                
            if image_label:
                image_label.image_data = image_blobs[idx]
                image_label.embedding = emb.astype(np.float32).tobytes()
                labels_to_save.append(image_label)
                
        if labels_to_save:
            self.repository.save_labels_batch(labels_to_save)
