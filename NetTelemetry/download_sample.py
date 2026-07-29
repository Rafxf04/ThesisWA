import urllib.request
import os

url = "https://wiki.wireshark.org/SampleCaptures?action=AttachFile&do=get&target=http.cap"
dest = "sample.pcap"

print(f"Downloading sample PCAP from {url}...")
try:
    urllib.request.urlretrieve(url, dest)
    print(f"Successfully downloaded to {dest}")
except Exception as e:
    print(f"Failed to download: {e}")
