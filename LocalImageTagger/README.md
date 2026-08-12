# ThesisWA - LocalImageTagger 🏷️

> **AI-Powered Local Image Tagging & Database Storage Engine**

`LocalImageTagger` is a modular Python application designed to automatically classify and tag local images using the **OpenAI CLIP (Contrastive Language-Image Pretraining)** model via OpenVINO for CPU-optimized inference. It leverages industry-standard software design patterns to provide a scalable architecture for image processing, classification via customizable strategies, and metadata storage in an SQLite database. It also features a Flask-based web UI for manual verification.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture & Design Patterns](#-architecture--design-patterns)
- [Project Structure](#-project-structure)
- [Installation & Quick Start](#-installation--quick-start)
- [Usage Guide](#-usage-guide)
- [Web Interface](#-web-interface)

---

## ✨ Features

- 🧠 **AI-Powered Inference**: Uses the HuggingFace `openai/clip-vit-base-patch32` model to match images against custom text prompts.
- ⚡ **OpenVINO CPU Optimization**: Optimized for fast local execution without requiring a dedicated GPU.
- 🏷️ **Smart Labeling**: Configurable confidence thresholds to determine direct matches or fallback to a default label.
- 🗄️ **SQLite Persistence**: Stores image metadata, binary data (thumbnails), inferred labels, and confidence scores in a local SQLite database.
- 📊 **Reporting**: Automatic generation of HTML reports summarizing the tagging results.
- 🌐 **Web UI**: A Flask application allowing users to visualize, review, and manually update the assigned labels.

---

## 🏗️ Architecture & Design Patterns

The codebase is built following clean architecture principles and software engineering design patterns:

### Applied Design Patterns

| Pattern | Location | Description |
| :--- | :--- | :--- |
| **Singleton** | `LocalImageTagger/src/core/engine.py` | **`ModelEngine`**: Thread-safe singleton that encapsulates the AI model loading (OpenVINO) and inference logic. Ensures the heavy CLIP model is loaded only once in memory. |
| **Strategy** | `LocalImageTagger/src/labeling/strategy.py` | **`LabelingStrategy`** / **`ThresholdFallbackStrategy`**: Interface and implementation for the labeling logic. Allows defining how the model's logits are converted into final tags based on threshold rules. |
| **Repository** | `LocalImageTagger/src/db/repository.py` | **`LabelRepository`**: Encapsulates all SQLite persistence logic and CRUD operations, abstracting the database schema from the core business logic. |
| **Facade / Controller** | `LocalImageTagger/src/core/processor.py` | **`ImageBatchProcessor`**: Orchestrates the interaction between the `ModelEngine`, the `LabelingStrategy`, and the `LabelRepository` to process images in batches. |

---

## 📁 Project Structure

```text
ThesisWA/
└── LocalImageTagger/
    ├── app.py                   # Flask Web UI entrypoint
    ├── main.py                  # CLI application entrypoint (Batch processing)
    ├── generate_report.py       # Script to generate HTML reports from DB
    ├── labels.txt               # Configuration file containing classification prompts
    ├── src/
    │   ├── core/
    │   │   ├── engine.py        # ModelEngine (Singleton for OpenVINO/CLIP)
    │   │   └── processor.py     # ImageBatchProcessor (Orchestrator)
    │   ├── db/
    │   │   ├── models.py        # Data classes representing database records
    │   │   └── repository.py    # LabelRepository (SQLite access)
    │   ├── labeling/
    │   │   └── strategy.py      # ThresholdFallbackStrategy
    │   └── utils/
    │       └── logger.py        # Centralized logging configuration
    └── scratch/
        └── migrate_embeddings.py# DB Migration utility script
```

---

## ⚙️ Installation & Quick Start

### 1. Set Up Virtual Environment

```bash
# Navigate to the project folder
cd ThesisWA/LocalImageTagger

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies

Install the required packages (e.g., `transformers`, `optimum[openvino]`, `Flask`, `Pillow`, etc.).
*(Make sure you have an appropriate `requirements.txt` available or manually install the dependencies).*

---

## 🚀 Usage Guide

### 1. Configure Labels
Edit the `labels.txt` file to define your custom categories. Format is `Prompt | Save_Name` (e.g. `A picture of a dog | Dog`).

### 2. Run the Tagger

Place your images in an `images/` directory, then run:

```bash
python main.py --images_dir images --labels_file labels.txt --batch_size 8 --threshold 0.85
```

This will analyze the images, determine the best label, and save the metadata and a thumbnail in `tags_database.sqlite`.

### 3. Generate HTML Report

```bash
python generate_report.py
```
This generates a static `report.html` file to preview the tagging results.

---

## 🌐 Web Interface

To manually review and correct the AI-assigned labels, start the Flask Web UI:

```bash
python app.py
```
Then navigate to `http://localhost:5000` in your web browser. You can browse all tagged images and update their labels interactively.
