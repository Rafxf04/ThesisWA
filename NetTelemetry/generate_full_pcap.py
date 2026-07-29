from scapy.all import *
load_layer("tls")

print("Generating full PCAP with HTTP, TLS (SNI), and DNS...")

# 1. HTTP Packet (Shows User-Agent extraction for App Identification)
http_req = (
    "GET / HTTP/1.1\r\n"
    "Host: example.com\r\n"
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36\r\n\r\n"
)
pkt_http = IP(src="192.168.1.50", dst="93.184.216.34")/TCP(sport=12345, dport=80)/Raw(load=http_req)

# 2. TLS Packet (Shows TLS SNI extraction for App Identification)
ch = TLSClientHello(
    version=0x0303,
    ext=[TLS_Ext_ServerName(servernames=[ServerName(servername="whatsapp.net")])]
)
tls = TLS(msg=[ch])
pkt_tls = IP(src="192.168.1.50", dst="157.240.22.60")/TCP(sport=12346, dport=443)/tls

# 3. DNS Packet
pkt_dns = IP(src="192.168.1.50", dst="8.8.8.8")/UDP(sport=12347, dport=53)/DNS(rd=1, qd=DNSQR(qname="www.google.com"))

# Write all to a pcap
wrpcap("full_sample.pcap", [pkt_http, pkt_tls, pkt_dns])
print("Done! Saved as full_sample.pcap")
