from flask import Flask, render_template, request, jsonify
from src.db.repository import LabelRepository
import base64

app = Flask(__name__)
repo = LabelRepository("tags_database.sqlite")

def get_all_labels():
    """
    Scopo: Recupera tutte le etichette dal file di configurazione locale.

    Parametri:
    - Nessuno

    Valore di ritorno:
    - list: Una lista ordinata e senza duplicati di stringhe rappresentanti le etichette.

    Eccezioni:
    - Nessuna eccezione prevista (FileNotFoundError gestita internamente).
    """
    labels = []
    try:
        with open("labels.txt", "r", encoding="utf-8") as f:
            for line in f:
                if "|" in line:
                    labels.append(line.split("|")[1].strip())
    except FileNotFoundError:
        pass
    return sorted(list(set(labels)))

def get_sorted_labels(repo, base_labels):
    """
    Scopo: Ordina le etichette in base alla loro frequenza di utilizzo nel database.

    Parametri:
    - repo (LabelRepository): Il repository per accedere ai dati delle etichette.
    - base_labels (list): La lista base di etichette da ordinare.

    Valore di ritorno:
    - list: Lista di etichette ordinata per frequenza decrescente e alfabeticamente.

    Eccezioni:
    - Nessuna eccezione prevista.
    """
    images = repo.get_labels()
    freq = {}
    for img in images:
        if img.label:
            freq[img.label] = freq.get(img.label, 0) + 1
            
    return sorted(base_labels, key=lambda x: (-freq.get(x, 0), x))

@app.route('/')
def index():
    """
    Scopo: Renderizza la pagina principale dell'interfaccia web con le immagini processate.

    Parametri:
    - Nessuno

    Valore di ritorno:
    - str: L'HTML renderizzato del template 'index.html'.

    Eccezioni:
    - Nessuna eccezione prevista.
    """
    images = repo.get_labels()
    
    base_labels = get_all_labels()
    all_labels = get_sorted_labels(repo, base_labels)
    
    processed_images = []
    for img in images:
        if img.image_data:
            b64 = base64.b64encode(img.image_data).decode('utf-8')
        else:
            b64 = ""
            
        processed_images.append({
            'id': img.id,
            'label': img.label,
            'score': img.score,
            'is_partial': img.is_partial,
            'user_verified': getattr(img, 'user_verified', False),
            'image_b64': b64
        })
        
    return render_template('index.html', images=processed_images, all_labels=all_labels)

@app.route('/api/update_label', methods=['POST'])
def update_label():
    """
    Scopo: Aggiorna l'etichetta associata a una specifica immagine tramite una chiamata API.

    Parametri:
    - Nessuno (i dati vengono estratti dal corpo della richiesta POST JSON)

    Valore di ritorno:
    - tuple: JSON response e codice HTTP (es. 200 per successo, 400 per errore).

    Eccezioni:
    - Nessuna eccezione prevista.
    """
    data = request.json
    label_id = data.get('id')
    new_label = data.get('label')
    
    if label_id is not None and new_label:
        repo.update_label(label_id, new_label)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid data"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
