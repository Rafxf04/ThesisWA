"""
Scopo: Genera un pacchetto PCAP di base (TCP e UDP) sintetico per effettuare quick test.
"""
import os
from scapy.all import *

output_dir = os.path.join(os.path.dirname(__file__), "pcaps")
os.makedirs(output_dir, exist_ok=True)
dest = os.path.join(output_dir, "synthetic_sample.pcap")

pkt1 = IP(dst="8.8.8.8")/TCP(dport=443)/Raw(b"Hello World TLS SNI simulation")
pkt2 = IP(dst="1.1.1.1")/UDP(dport=53)/Raw(b"DNS query simulation")

wrpcap(dest, [pkt1, pkt2])
print(f"Generated {dest}")
