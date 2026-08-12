"""
Scopo: Script per scaricare un PCAP di esempio (traffico HTTP) per effettuare i test del sistema.
"""
import urllib.request
import os

url = "https://raw.githubusercontent.com/wireshark/wireshark/master/test/captures/http.pcap"
output_dir = os.path.join(os.path.dirname(__file__), "pcaps")
os.makedirs(output_dir, exist_ok=True)
dest = os.path.join(output_dir, "sample.pcap")

print(f"Downloading sample PCAP from {url}...")
try:
    req = urllib.request.Request(url, headers={"User-Agent": "NetTelemetry/1.0"})
    with urllib.request.urlopen(req) as response, open(dest, 'wb') as out_file:
        out_file.write(response.read())
    print(f"Successfully downloaded to {dest}")
except Exception as e:
    print(f"Failed to download: {e}")
