import os
import argparse
from src.core.engine import ModelEngine
from src.core.processor import ImageBatchProcessor
from src.labeling.strategy import ThresholdFallbackStrategy
from src.db.repository import LabelRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)

def load_labels_from_file(file_path: str) -> list[dict]:
    """
    Scopo: Carica le etichette da un file di testo, formattandole in una lista di dizionari.

    Parametri:
    - file_path (str): Il percorso del file di testo contenente le etichette.

    Valore di ritorno:
    - list[dict]: Lista di dizionari con chiavi 'prompt' e 'save_name'.

    Eccezioni:
    - Nessuna eccezione prevista.
    """
    if not os.path.exists(file_path):
        logger.error(f"File etichette {file_path} non trovato.")
        return []
    
    labels = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split("|")
            if len(parts) == 2:
                labels.append({"prompt": parts[0].strip(), "save_name": parts[1].strip()})
            else:
                labels.append({"prompt": parts[0].strip(), "save_name": parts[0].strip()})
    return labels

def main():
    """
    Scopo: Avvia il processo di elaborazione delle immagini, applicando pattern architetturali (Singleton, Strategy, Repository) per classificare e memorizzare i tag.

    Parametri:
    - Nessuno (i parametri vengono letti da linea di comando tramite argparse)

    Valore di ritorno:
    - Nessuno

    Eccezioni:
    - Nessuna eccezione prevista.
    """
    parser = argparse.ArgumentParser(description="Local AI Image Tagger ottimizzato per CPU")
    parser.add_argument("--images_dir", type=str, default="images", help="Cartella contenente le immagini")
    parser.add_argument("--labels_file", type=str, default="labels.txt", help="File di testo con i temi (uno per riga)")
    parser.add_argument("--batch_size", type=int, default=8, help="Dimensione del batch per l'inferenza")
    parser.add_argument("--threshold", type=float, default=0.85, help="Soglia per il match diretto (0.0 - 1.0)")
    
    args = parser.parse_args()

    os.makedirs(args.images_dir, exist_ok=True)

    logger.info("Inizializzazione sistema...")
    labels = load_labels_from_file(args.labels_file)
    if not labels:
        logger.error("Nessuna etichetta caricata. Termino.")
        return

    logger.info(f"Etichette caricate: {labels}")

    engine = ModelEngine(model_id="openai/clip-vit-base-patch32")
    
    strategy = ThresholdFallbackStrategy(threshold=args.threshold)
    
    repository = LabelRepository(db_path="tags_database.sqlite")
    
    processor = ImageBatchProcessor(
        engine=engine,
        strategy=strategy,
        repository=repository,
        batch_size=args.batch_size
    )

    logger.info(f"Inizio elaborazione immagini nella cartella: {args.images_dir}")
    processor.process_directory(args.images_dir, labels)
    logger.info("Elaborazione completata.")

if __name__ == "__main__":
    main()
