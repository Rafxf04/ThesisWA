import sqlite3
from typing import List
from src.db.models import ImageLabel

class LabelRepository:
    """
    Repository Pattern: Gestisce le operazioni di persistenza dei dati (CRUD) sul database SQLite.
    Isola la logica di accesso ai dati dal resto dell'applicazione.
    """
    def __init__(self, db_path: str = "labels.sqlite"):
        """
        Scopo: Inizializza il repository con il percorso del database.

        Parametri:
        - db_path (str): Il percorso al file di database SQLite.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """
        Scopo: Crea la tabella image_labels se non esiste già.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - sqlite3.Error: In caso di errore durante la creazione della tabella.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS image_labels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL,
                    image_data BLOB,
                    label TEXT NOT NULL,
                    score REAL NOT NULL,
                    is_partial BOOLEAN NOT NULL,
                    user_verified BOOLEAN NOT NULL DEFAULT 0,
                    embedding BLOB
                )
            """)
            conn.commit()

    def save_label(self, label: ImageLabel) -> int:
        """
        Scopo: Salva una singola etichetta immagine nel database.

        Parametri:
        - label (ImageLabel): L'oggetto ImageLabel da salvare.

        Valore di ritorno:
        - int: L'ID del record inserito nel database.

        Eccezioni:
        - sqlite3.Error: In caso di fallimento nell'inserimento del record.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO image_labels (image_path, image_data, label, score, is_partial, user_verified, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (label.image_path, label.image_data, label.label, label.score, label.is_partial, label.user_verified, label.embedding))
            conn.commit()
            return cursor.lastrowid

    def save_labels_batch(self, labels: List[ImageLabel]):
        """
        Scopo: Salva un batch multiplo di etichette immagine nel database.

        Parametri:
        - labels (List[ImageLabel]): Una lista di oggetti ImageLabel da salvare contemporaneamente.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - sqlite3.Error: In caso di fallimento nell'inserimento dei record.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO image_labels (image_path, image_data, label, score, is_partial, user_verified, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [(l.image_path, l.image_data, l.label, l.score, l.is_partial, l.user_verified, l.embedding) for l in labels])
            conn.commit()

    def get_labels(self) -> List[ImageLabel]:
        """
        Scopo: Recupera tutte le etichette immagine memorizzate.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - List[ImageLabel]: Una lista di oggetti ImageLabel rappresentanti tutte le righe.

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, image_path, image_data, label, score, is_partial, user_verified, embedding FROM image_labels")
            rows = cursor.fetchall()
            return [
                ImageLabel(
                    id=row[0],
                    image_path=row[1],
                    image_data=row[2],
                    label=row[3],
                    score=row[4],
                    is_partial=bool(row[5]),
                    user_verified=bool(row[6]),
                    embedding=row[7]
                ) for row in rows
            ]

    def get_verified_embeddings(self) -> List[ImageLabel]:
        """
        Scopo: Recupera gli embedding delle immagini con etichetta validata manualmente.

        Parametri:
        - Nessuno

        Valore di ritorno:
        - List[ImageLabel]: Una lista di ImageLabel contenenti solo ID, path, etichetta ed embedding per uso in match di similarità.

        Eccezioni:
        - Nessuna eccezione prevista.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, image_path, label, embedding FROM image_labels WHERE user_verified = 1 AND embedding IS NOT NULL")
            rows = cursor.fetchall()
            return [
                ImageLabel(
                    id=row[0],
                    image_path=row[1],
                    label=row[2],
                    embedding=row[3],
                    score=1.0,
                    is_partial=False
                ) for row in rows
            ]

    def update_label(self, label_id: int, new_label: str, embedding: bytes = None):
        """
        Scopo: Aggiorna l'etichetta associata a un ID e marca il record come verificato dall'utente.

        Parametri:
        - label_id (int): L'ID del record da aggiornare.
        - new_label (str): La nuova etichetta corretta.
        - embedding (bytes, opzionale): Il vettore aggiornato da memorizzare nel caso sia necessario.

        Valore di ritorno:
        - Nessuno

        Eccezioni:
        - sqlite3.Error: In caso di errore durante l'aggiornamento.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if embedding is not None:
                cursor.execute("""
                    UPDATE image_labels 
                    SET label = ?, user_verified = 1, embedding = ?
                    WHERE id = ?
                """, (new_label, embedding, label_id))
            else:
                cursor.execute("""
                    UPDATE image_labels 
                    SET label = ?, user_verified = 1 
                    WHERE id = ?
                """, (new_label, label_id))
            conn.commit()
