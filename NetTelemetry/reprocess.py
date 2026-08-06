import urllib.request
import urllib.parse
import subprocess
import time

tables = ["Tema1", "Tema2", "Tema3", "Tema4", "Tema5"]
host = "http://localhost:9000/exec"

print("Dropping existing tables in QuestDB to replace data...")
for table in tables:
    query = f"DROP TABLE IF EXISTS {table};"
    url = f"{host}?query={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            print(f"Dropped {table}: {response.read().decode('utf-8')}")
    except Exception as e:
        print(f"Error dropping {table}: {e}")

print("\nRunning run_all.py to re-extract all data...")
subprocess.run(["venv\\Scripts\\python.exe", "run_all.py"])
print("Reprocessing complete!")
