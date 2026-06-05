<p align="center">
  <img src="app/app_icon.png" width="120" alt="Slate Icon">
</p>

<h1 align="center">Slate</h1>

<p align="center">
  <strong>A fast, keyboard-driven PDF reader & annotator.</strong>
</p>

<p align="center">
  <img src="assets/Sidebar.png" width="48%" alt="Slate Sidebar">
  <img src="assets/Annotations.png" width="48%" alt="Slate Annotations">
</p>

---

**Slate** is a lightweight desktop app built for reading PDFs and taking notes quickly. Instead of dealing with slow, bloated PDF suites, Slate focuses on speed, instant startup, and a completely keyboard-driven workflow.

---

## Why Slate?

* **Low Memory Usage:** Dynamically loads and unloads pages as you scroll, easily handling 1000+ page books without memory lag.
* **Keyboard-First:** Switch tools, change colors, zoom, and navigate pages using single-key shortcuts.

---

## Keyboard Shortcuts

| Key | Tool / Action | Description |
| :--- | :--- | :--- |
| **`V`** | **Select Text** | Select blocks. Press **`Ctrl + C`** to copy. |
| **`H`** | **Highlight** | Highlight text in active color. |
| **`P`** | **Pen** | Draw/sketch freely. |
| **`T`** | **Text** | Click to type text. Click existing text to edit/drag. |
| **`S`** | **Square** | Draw a rectangle/square outline shape. |
| **`A`** | **Arrow** | Draw an arrow shape. |
| **`E`** | **Eraser** | Click/drag over any annotation to delete it. |
| **`R`** | **Rect Selection** | Toggle rectangle-box selection mode on/off. |
| **`1` - `5`** | **Colors** | Yellow (`1`), Blue (`2`), Green (`3`), Red (`4`), Black (`5`). |
| **`O` / `0` / `F9`** | **Toggle Outline** | Toggle the Table of Contents / Outline sidebar. |
| **`J` / `K`** | **Vim Scroll** | Scroll vertical canvas down / up smoothly. |
| **`Ctrl + S`** | **Save** | Save edits directly to the PDF file. |
| **`Ctrl + O`** | **Open** | Open a new PDF. |
| **`Ctrl + =` / `-`** | **Zoom** | Zoom In / Zoom Out. |
| **`Left` / `Right`** | **Navigate** | Go to the previous / next page. |

---

## Installation (Ubuntu/Debian)

1. Download **`slate_1.0_amd64.deb`** from the [Releases](https://github.com/sharjeel103/slate/releases) tab.
2. Install it via terminal:
   ```bash
   sudo apt install ./slate_1.0_amd64.deb
   ```
3. Run the app by typing `slate` in your terminal or launching it from your desktop applications menu.

---

## Developer Setup

To run from source:

```bash
# 1. Clone & enter dir
git clone https://github.com/sharjeel103/slate.git
cd slate

# 2. Setup environment & install packages
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run
python main.py
```
To rebuild the `.deb` package:

```bash
# Build default version 1.0
./build_deb.sh

# Or specify a custom version
./build_deb.sh 1.1
```
