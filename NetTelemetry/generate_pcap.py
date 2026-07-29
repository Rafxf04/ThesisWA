from scapy.all import *

# Create a sample packet with an IP and TCP layer
pkt1 = IP(dst="8.8.8.8")/TCP(dport=443)/Raw(b"Hello World TLS SNI simulation")
pkt2 = IP(dst="1.1.1.1")/UDP(dport=53)/Raw(b"DNS query simulation")

wrpcap("sample.pcap", [pkt1, pkt2])
print("Generated sample.pcap")
