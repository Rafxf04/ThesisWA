"""
Regenerate tema1-tema5 dashboard JSON files with corrected time filter macros.
Uses: timestamp >= $__timeFrom() AND timestamp <= $__timeTo()
Instead of the broken: $__timeFilter(timestamp)
"""
import json
import os
import urllib.request
import urllib.parse

def get_time_bounds(table_name):
    try:
        query = urllib.parse.quote(f"SELECT min(timestamp), max(timestamp) FROM {table_name}")
        url = f"http://localhost:9000/exec?query={query}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get("dataset") and len(data["dataset"]) > 0:
                min_ts, max_ts = data["dataset"][0]
                if min_ts and max_ts:
                    return min_ts, max_ts
    except Exception as e:
        print(f"Warning: could not fetch time bounds for {table_name}: {e}")
    return "now-7d", "now"

TIME_FILTER = "1=1"

def make_datasource(uid="QuestDB"):
    return {
        "type": "questdb-questdb-datasource",
        "uid": uid
    }

def make_target(query, uid="QuestDB", format_type=None):
    target = {
        "datasource": make_datasource(uid),
        "rawSql": query,
        "query": query,
        "refId": "A"
    }
    if format_type:
        target["format"] = format_type
    return target

def make_panel(id, title, panel_type, query, gridPos, uid="QuestDB", extra_options=None, extra_field_config=None, transformations=None):
    format_type = None if panel_type == "timeseries" else "table"
    panel = {
        "collapsed": False,
        "gridPos": gridPos,
        "id": id,
        "title": title,
        "type": panel_type,
        "datasource": make_datasource(uid),
        "targets": [make_target(query, uid, format_type)]
    }
    if extra_options:
        panel["options"] = extra_options
    if extra_field_config:
        panel["fieldConfig"] = extra_field_config
    if transformations:
        panel["transformations"] = transformations
    return panel
    
PIE_OPTIONS = {
    "reduceOptions": {"values": True, "calcs": [], "fields": ""},
    "pieType": "pie",
    "tooltip": {"mode": "single", "sort": "none"},
    "displayLabels": ["percent", "name"],
    "legend": {"displayMode": "list", "placement": "right", "calcs": []}
}


def generate_tema_dashboard(tema_num):
    table_name = f"Tema{tema_num}"
    tf = TIME_FILTER

    panels = []

    # === Row: Tema 1 - Panoramica KPI e Metriche Globali ===
    panels.append({
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0},
        "id": 100,
        "title": f"\U0001f3e0 Panoramica KPI e Metriche Globali (Tabella: {table_name})",
        "type": "row"
    })

    # Total Captured Packets
    panels.append(make_panel(
        id=1, title="Total Captured Packets", panel_type="stat",
        query=f"SELECT count(*) FROM {table_name} WHERE {tf};",
        gridPos={"h": 4, "w": 5, "x": 0, "y": 1},
        extra_options={
            "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""},
            "orientation": "auto", "textMode": "auto", "colorMode": "value"
        }
    ))

    # Total Bytes Processed
    panels.append(make_panel(
        id=2, title="Total Bytes Processed", panel_type="stat",
        query=f"SELECT sum(length) FROM {table_name} WHERE {tf};",
        gridPos={"h": 4, "w": 5, "x": 5, "y": 1},
        extra_field_config={"defaults": {"unit": "bytes"}}
    ))

    # Average Packet Size
    panels.append(make_panel(
        id=3, title="Average Packet Size (bytes)", panel_type="stat",
        query=f"SELECT avg(length) FROM {table_name} WHERE {tf};",
        gridPos={"h": 4, "w": 5, "x": 10, "y": 1},
        extra_field_config={"defaults": {"unit": "bytes", "decimals": 2}}
    ))

    # Unique Source Hosts
    panels.append(make_panel(
        id=4, title="Unique Source Hosts", panel_type="stat",
        query=f"SELECT count(DISTINCT src_ip) FROM {table_name} WHERE {tf};",
        gridPos={"h": 4, "w": 5, "x": 15, "y": 1}
    ))

    # Unique Destination Hosts
    panels.append(make_panel(
        id=5, title="Unique Destination Hosts", panel_type="stat",
        query=f"SELECT count(DISTINCT dst_ip) FROM {table_name} WHERE {tf};",
        gridPos={"h": 4, "w": 4, "x": 20, "y": 1}
    ))

    # === Row: Tema 2 - Analisi Temporale e Throughput ===
    panels.append({
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": 5},
        "id": 200,
        "title": f"\U0001f4c8 Analisi Temporale e Throughput di Rete (Tabella: {table_name})",
        "type": "row"
    })

    # Packet Rate over Time
    panels.append(make_panel(
        id=6, title="Packet Rate over Time (Packets / sec)", panel_type="timeseries",
        query=f"SELECT timestamp, count(*) as packet_rate FROM {table_name} WHERE {tf} SAMPLE BY 1s ALIGN TO CALENDAR;",
        gridPos={"h": 8, "w": 12, "x": 0, "y": 6}
    ))

    # Data Throughput
    panels.append(make_panel(
        id=7, title="Data Throughput (Bytes / sec)", panel_type="timeseries",
        query=f"SELECT timestamp, sum(length) as total_bytes FROM {table_name} WHERE {tf} SAMPLE BY 1s ALIGN TO CALENDAR;",
        gridPos={"h": 8, "w": 12, "x": 12, "y": 6},
        extra_field_config={"defaults": {"unit": "bytes"}}
    ))

    # === Row: Tema 3 - Protocolli e Porte ===
    panels.append({
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": 14},
        "id": 300,
        "title": f"\U0001f310 Protocolli di Rete e Analisi delle Porte (Tabella: {table_name})",
        "type": "row"
    })

    # Protocol Distribution
    panels.append(make_panel(
        id=8, title="Distribuzione Protocolli", panel_type="piechart",
        query=f"SELECT protocol, count(*) as count FROM {table_name} WHERE {tf} AND protocol != 'Unknown' GROUP BY protocol;",
        gridPos={"h": 8, "w": 8, "x": 0, "y": 14},
        extra_options=PIE_OPTIONS
    ))

    # Top Destination Ports
    panels.append(make_panel(
        id=9, title="Top Destination Ports (Packet Count)", panel_type="barchart",
        query=f"SELECT dst_port, count(*) as count FROM {table_name} WHERE {tf} GROUP BY dst_port ORDER BY count DESC LIMIT 10;",
        gridPos={"h": 8, "w": 8, "x": 8, "y": 15},
        transformations=[{"id": "convertFieldType", "options": {"conversions": [{"destinationType": "string", "targetField": "dst_port"}], "fields": {}}}]
    ))

    # Top Source Ports by Bytes
    panels.append(make_panel(
        id=10, title="Top Source Ports (Volume Byte)", panel_type="barchart",
        query=f"SELECT src_port, sum(length) as total_bytes FROM {table_name} WHERE {tf} GROUP BY src_port ORDER BY total_bytes DESC LIMIT 10;",
        gridPos={"h": 8, "w": 8, "x": 16, "y": 15},
        transformations=[{"id": "convertFieldType", "options": {"conversions": [{"destinationType": "string", "targetField": "src_port"}], "fields": {}}}]
    ))

    # === Row: Tema 4 - Servizi e Applicazioni ===
    panels.append({
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": 23},
        "id": 400,
        "title": f"\U0001f4f1 Servizi Applicativi e Deep Packet Inspection (Tabella: {table_name})",
        "type": "row"
    })

    # Top Services
    panels.append(make_panel(
        id=11, title="Top Network Services (Packet Count)", panel_type="barchart",
        query=f"SELECT service_name, count(*) as count FROM {table_name} WHERE {tf} GROUP BY service_name ORDER BY count DESC LIMIT 10;",
        gridPos={"h": 8, "w": 8, "x": 0, "y": 24}
    ))

    # Top Applications by Bytes
    panels.append(make_panel(
        id=12, title="Top Applications (Volume Byte)", panel_type="barchart",
        query=f"SELECT dst_app_name, sum(length) as total_bytes FROM {table_name} WHERE {tf} AND dst_app_name != 'Local Network' GROUP BY dst_app_name ORDER BY total_bytes DESC LIMIT 10;",
        gridPos={"h": 8, "w": 8, "x": 8, "y": 24}
    ))

    # TLS/SNI Analysis
    panels.append(make_panel(
        id=13, title="TLS/SNI Connections Analysis", panel_type="table",
        query=f"SELECT tls_sni, count(*) as tls_connections, sum(length) as total_bytes FROM {table_name} WHERE {tf} AND length(tls_sni) > 0 GROUP BY tls_sni ORDER BY tls_connections DESC LIMIT 10;",
        gridPos={"h": 8, "w": 8, "x": 16, "y": 24}
    ))

    # === Row: Tema 5 - Geolocalizzazione ===
    panels.append({
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": 32},
        "id": 500,
        "title": f"\U0001f30d Geolocalizzazione e Distribuzione Geografica (Tabella: {table_name})",
        "type": "row"
    })

    # Traffic by Country
    panels.append(make_panel(
        id=14, title="Traffic by Destination Country", panel_type="barchart",
        query=f"SELECT geo_country, count(*) as count FROM {table_name} WHERE {tf} AND geo_country NOT IN ('Local', 'Local Network', 'Unknown') GROUP BY geo_country ORDER BY count DESC LIMIT 10;",
        gridPos={"h": 8, "w": 12, "x": 0, "y": 33}
    ))

    # Top Foreign Countries by Volume
    panels.append(make_panel(
        id=15, title="Top Foreign Countries (Volume Byte)", panel_type="table",
        query=f"SELECT geo_country, count(*) as packet_count, sum(length) as total_bytes FROM {table_name} WHERE {tf} AND geo_country NOT IN ('Local', 'Local Network', 'Unknown') GROUP BY geo_country ORDER BY total_bytes DESC LIMIT 10;",
        gridPos={"h": 8, "w": 12, "x": 12, "y": 33}
    ))

    # === Row: Tema 6 - Host e Conversazioni ===
    panels.append({
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": 41},
        "id": 600,
        "title": f"\U0001f4bb Host, Conversazioni e Log dei Flussi (Tabella: {table_name})",
        "type": "row"
    })

    # Top Talkers (Source)
    panels.append(make_panel(
        id=16, title="Top Talkers (IP Sorgente)", panel_type="table",
        query=f"SELECT src_ip, src_app_name, count(*) as packets_sent, sum(length) as bytes_sent FROM {table_name} WHERE {tf} AND src_app_name != 'Local Network' GROUP BY src_ip, src_app_name ORDER BY bytes_sent DESC LIMIT 10;",
        gridPos={"h": 8, "w": 12, "x": 0, "y": 42}
    ))

    # Top Receivers (Destination)
    panels.append(make_panel(
        id=17, title="Top Receivers (IP Destinazione)", panel_type="table",
        query=f"SELECT dst_ip, dst_app_name, geo_country, count(*) as packets_received, sum(length) as bytes_received FROM {table_name} WHERE {tf} AND dst_app_name != 'Local Network' GROUP BY dst_ip, dst_app_name, geo_country ORDER BY bytes_received DESC LIMIT 10;",
        gridPos={"h": 8, "w": 12, "x": 12, "y": 42}
    ))

    # Recent Packet Flow Logs
    panels.append(make_panel(
        id=18, title="Recent Live Packet Flow Logs", panel_type="table",
        query=f"SELECT * FROM (SELECT timestamp, src_app_name, dst_app_name, geo_country, length FROM {table_name} WHERE {tf} ORDER BY timestamp DESC LIMIT 100) ORDER BY timestamp ASC;",
        gridPos={"h": 10, "w": 24, "x": 0, "y": 50},
        transformations=[{"id": "sortBy", "options": {"fields": {}, "sort": [{"desc": True, "field": "timestamp"}]}}]
    ))

    # === Row: Tema 7 - Sicurezza ===
    panels.append({
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": 60},
        "id": 700,
        "title": f"\U0001f6e1\ufe0f Sicurezza di Rete e Anomalie (Tabella: {table_name})",
        "type": "row"
    })

    # Port Scanning Detection (subquery to avoid HAVING, unsupported by QuestDB)
    panels.append(make_panel(
        id=19, title="Port Scanning Detection (Host contattando porte multiple)", panel_type="table",
        query=f"SELECT * FROM (SELECT src_ip, count(DISTINCT dst_port) as unique_ports_targeted, count(*) as total_packets FROM {table_name} WHERE {tf} GROUP BY src_ip ORDER BY unique_ports_targeted DESC) WHERE unique_ports_targeted > 5;",
        gridPos={"h": 8, "w": 12, "x": 0, "y": 61}
    ))

    # Unknown Traffic
    panels.append(make_panel(
        id=20, title="Traffico Non Classificato (Unknown Services)", panel_type="timeseries",
        query=f"SELECT timestamp, count(*) as unknown_packets, sum(length) as unknown_bytes FROM {table_name} WHERE {tf} AND service_name = 'Unknown' SAMPLE BY 1m ALIGN TO CALENDAR;",
        gridPos={"h": 8, "w": 12, "x": 12, "y": 61}
    ))

    # === Row: Tema 8 - Analisi Profonda Protocolli ===
    panels.append({
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": 70},
        "id": 800,
        "title": f"\U0001f50d Analisi Profonda Protocolli (HTTP, DNS, TLS) (Tabella: {table_name})",
        "type": "row"
    })

    # HTTP Top Hosts
    panels.append(make_panel(
        id=21, title="HTTP - Top Hosts Richiesti", panel_type="barchart",
        query=f"SELECT http_host, count(*) as requests FROM {table_name} WHERE {tf} AND length(http_host) > 0 GROUP BY http_host ORDER BY requests DESC LIMIT 10;",
        gridPos={"h": 8, "w": 8, "x": 0, "y": 71}
    ))

    # HTTP Methods
    panels.append(make_panel(
        id=22, title="HTTP - Metodi Utilizzati", panel_type="piechart",
        query=f"SELECT http_method, count(*) as count FROM {table_name} WHERE {tf} AND length(http_method) > 0 GROUP BY http_method;",
        gridPos={"h": 8, "w": 8, "x": 8, "y": 71},
        extra_options=PIE_OPTIONS
    ))

    # DNS Queries
    panels.append(make_panel(
        id=23, title="DNS - Top Query Risolte", panel_type="table",
        query=f"SELECT dns_query, count(*) as query_count FROM {table_name} WHERE {tf} AND length(dns_query) > 0 GROUP BY dns_query ORDER BY query_count DESC LIMIT 10;",
        gridPos={"h": 8, "w": 8, "x": 16, "y": 71}
    ))

    # TLS Versions
    tls_case = "CASE tls_version WHEN '0x0304' THEN 'TLS 1.3' WHEN '0x0303' THEN 'TLS 1.2' WHEN '0x0302' THEN 'TLS 1.1' WHEN '0x0301' THEN 'TLS 1.0' WHEN '0x0300' THEN 'SSL 3.0' WHEN '0x0002' THEN 'SSL 2.0' ELSE tls_version END"
    panels.append(make_panel(
        id=24, title="TLS - Versioni Negoziate", panel_type="piechart",
        query=f"SELECT {tls_case} as tls_version, count(*) as count FROM {table_name} WHERE {tf} AND length(tls_version) > 0 GROUP BY tls_version;",
        gridPos={"h": 8, "w": 8, "x": 0, "y": 79},
        extra_options=PIE_OPTIONS
    ))

    # Payload Logs
    panels.append(make_panel(
        id=25, title="Dati in Chiaro (Payload Preview)", panel_type="table",
        query=f"SELECT * FROM (SELECT timestamp, src_ip, dst_ip, protocol, dst_port, payload_len, payload_preview FROM {table_name} WHERE {tf} AND length(payload_preview) > 0 ORDER BY timestamp DESC LIMIT 50) AS recent_data ORDER BY timestamp ASC;",
        gridPos={"h": 8, "w": 16, "x": 8, "y": 79},
        transformations=[{"id": "sortBy", "options": {"fields": {}, "sort": [{"desc": True, "field": "timestamp"}]}}]
    ))


    min_ts, max_ts = get_time_bounds(table_name)
    dashboard = {
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "id": None,
        "links": [],
        "liveNow": False,
        "refresh": "5s",
        "schemaVersion": 38,
        "style": "dark",
        "tags": ["nettelemetry", "questdb", "pcap"],
        "time": {"from": min_ts, "to": max_ts},
        "timepicker": {
            "refresh_intervals": ["5s", "10s", "30s", "1m"]
        },
        "timezone": "browser",
        "title": f"NetTelemetry - Dashboard per {table_name}",
        "uid": f"nettelemetry-tema{tema_num}",
        "panels": panels
    }

    return dashboard


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))

    for tema_num in range(1, 6):
        dashboard = generate_tema_dashboard(tema_num)
        filename = f"tema{tema_num}_dashboard.json"
        filepath = os.path.join(base_dir, filename)

        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False)

        size = os.path.getsize(filepath)
        print(f"Generated {filename}: {size} bytes")

    print("\nDone! All 5 dashboard files regenerated with fixed time filter macros.")
