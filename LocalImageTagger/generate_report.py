import sqlite3
import base64
import os

def generate_html():
    """
    Scopo: Genera un report HTML contenente le immagini e le relative etichette dal database.

    Parametri:
    - Nessuno

    Valore di ritorno:
    - Nessuno

    Eccezioni:
    - Nessuna eccezione prevista.
    """
    if not os.path.exists("tags_database.sqlite"):
        print("Database non trovato.")
        return

    conn = sqlite3.connect("tags_database.sqlite")
    cursor = conn.cursor()
    cursor.execute("SELECT image_path, image_data, label, score, is_partial FROM image_labels")
    rows = cursor.fetchall()

    html = """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Report Etichettatura AI</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #e0e0e0; padding: 20px; }
            h1 { text-align: center; color: #ffffff; margin-bottom: 30px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
            .card { background: #1e1e1e; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.5); display: flex; flex-direction: column; transition: transform 0.2s; }
            .card:hover { transform: scale(1.02); }
            .card img { width: 100%; height: 300px; object-fit: cover; }
            .info { padding: 15px; }
            .label { font-size: 1.2em; font-weight: bold; color: #4db8ff; }
            .score { font-size: 0.9em; color: #aaaaaa; margin-top: 5px; }
            .partial { color: #ff5252; font-weight: bold; font-size: 0.8em; margin-top: 5px; }
        </style>
    </head>
    <body>
        <h1>Risultati Etichettatura AI</h1>
        <div class="grid">
    """

    for row in rows:
        path, img_data, label, score, is_partial = row
        img_b64 = base64.b64encode(img_data).decode('utf-8')
        
        html += f"""
            <div class="card">
                <img src="data:image/jpeg;base64,{img_b64}" alt="{label}" loading="lazy">
                <div class="info">
                    <div class="label">🏷️ {label}</div>
                    <div class="score">Affinità: {score:.2f}</div>
                    {f'<div class="partial">⚠️ Match Parziale (Sotto Soglia)</div>' if is_partial else ''}
                </div>
            </div>
        """

    html += """
        </div>
    </body>
    </html>
    """

    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    print("Report generato con successo! Apri report.html nel tuo browser.")

if __name__ == "__main__":
    generate_html()
