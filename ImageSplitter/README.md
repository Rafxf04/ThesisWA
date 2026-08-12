# ThesisWA - ImageSplitter ✂️

> **Social Feed Manual Image Splitter Utility**

`ImageSplitter` is a lightweight, intuitive GUI application built with Python and Tkinter. It is designed to help content creators and developers manually split long, vertically-scrolling images (such as social media feeds or tall infographics) into multiple individual posts/segments. 

---

## 📋 Table of Contents

- [Features](#-features)
- [Project Structure](#-project-structure)
- [Installation & Quick Start](#-installation--quick-start)
- [Usage Guide](#-usage-guide)

---

## ✨ Features

- 🖼️ **Interactive GUI**: User-friendly Tkinter interface with scroll and zoom capabilities.
- 🎯 **Precise Cutting**: Add, adjust, or remove horizontal cut lines directly on the image with a simple click.
- 🔍 **Zoom Controls**: Use the mouse wheel or GUI buttons to zoom in/out for pixel-perfect precision.
- 💾 **Auto-Export**: Automatically slices the image at the selected boundaries and saves the segments into a structured output folder.

---

## 📁 Project Structure

```text
ThesisWA/
└── ImageSplitter/
    └── app.py                   # Main Tkinter Application Entrypoint
```

---

## ⚙️ Installation & Quick Start

### 1. Set Up Virtual Environment

```bash
# Navigate to the project folder
cd ThesisWA/ImageSplitter

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies

The application relies on `Pillow` for image manipulation and `tkinter` (which is typically included with standard Python installations).

```bash
pip install Pillow
```

---

## 🚀 Usage Guide

1. **Launch the Application**:
   ```bash
   python app.py
   ```
2. **Select an Image**: Click the "Seleziona Immagine" button to open a file dialog and load your target image (JPG, PNG, WEBP, etc.).
3. **Set Cut Points**: 
   - Scroll through the image using the scrollbars or mouse wheel.
   - Use the `Zoom In (+)` and `Zoom Out (-)` buttons to adjust your view.
   - **Click** anywhere on the image to place a red dashed cutline.
   - **Click again** near an existing line to remove it.
4. **Export**: Click the blue `FATTO - RITAGLIA ORA` button. The application will crop the image into segments and save them into a new folder named `<original_filename>_splits` next to your original file. The folder will automatically open upon completion.
