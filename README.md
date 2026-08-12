# ThesisWA - Thesis Applications Portfolio 🎓

Welcome to the **ThesisApps** monorepo! This repository contains a collection of three independent software applications developed as part of a thesis project. Each application serves a distinct purpose and is built using modern software engineering practices, clean architecture, and well-known design patterns.

---

## 📂 Projects Overview

Below is a brief summary of the three applications contained in this repository. Click on the project name to navigate to its dedicated directory and read the full documentation.

### 1. [NetTelemetry](./NetTelemetry/) 🚀
> **High-Performance, Design-Pattern-Driven Packet Capture (PCAP) Analytics & Storage Engine**

A modular, enterprise-grade Python application designed to parse, analyze, enrich, and store network traffic statistics from `.pcap` files. 
- **Core Tech**: Python, PyShark, QuestDB (Influx Line Protocol), Grafana.
- **Key Features**: Deep Packet Inspection (DPI), GeoIP/ASN enrichment, time-series storage, automated Grafana dashboards.
- **Patterns**: Facade, Observer, Strategy, Repository, Proxy/Decorator.

### 2. [LocalImageTagger](./LocalImageTagger/) 🏷️
> **AI-Powered Local Image Tagging & Database Storage Engine**

An intelligent utility to automatically classify and tag local images using the **OpenAI CLIP** model optimized for CPU inference.
- **Core Tech**: Python, OpenVINO, HuggingFace, SQLite, Flask.
- **Key Features**: CPU-optimized inference, custom prompt thresholding, SQLite persistence, local Flask-based Web UI for manual review, HTML report generation.
- **Patterns**: Singleton, Strategy, Repository, Facade.

### 3. [ImageSplitter](./ImageSplitter/) ✂️
> **Social Feed Manual Image Splitter Utility**

A lightweight, intuitive GUI application built to help content creators manually split long, vertically-scrolling images (like social media feeds) into individual posts.
- **Core Tech**: Python, Tkinter, Pillow.
- **Key Features**: Interactive GUI with zoom/scroll, point-and-click cutlines, automated cropping and export.

---

## 🛠️ General Prerequisites

While each project has its own specific dependencies (detailed in their respective `README.md` files), the base requirements for running the tools in this repository are:

- **Python 3.8+**
- **Git** (for version control)
- **Docker & Docker Compose** (Required only for `NetTelemetry` to run the database and visualization infrastructure).

---

## 🚀 Getting Started

To get started with any of the projects, clone the repository and navigate to the specific project folder:

```bash
git clone https://github.com/Rafxf04/ThesisWA.git
cd ThesisWA

# Navigate to the project you want to use, for example:
cd NetTelemetry
```

From there, follow the instructions provided in the `README.md` file located inside the project folder.

---

## 📄 License

This repository is intended for academic, research, and educational purposes. Please refer to the [LICENSE](LICENSE) file for more details.
