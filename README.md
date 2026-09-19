# Building Change to CAD (QGIS Plugin) 🏢🛰️

![QGIS Plugin](https://img.shields.io/badge/QGIS-Plugin-green?logo=qgis)
![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![License](https://img.shields.io/badge/License-GPLv2-brightgreen)

Building Change to CAD is a QGIS plugin for detecting building changes from satellite imagery and exporting the results directly to CAD.

The plugin uses NDBI (Normalized Difference Built-up Index) to identify built-up areas and compare changes between two dates. The detected changes are converted into vector polygons and exported as DXF, making them easier to use in AutoCAD and other CAD-based workflows.

---

## 📌 Features

- **NDBI Calculation** – Calculates NDBI from SWIR and NIR imagery.
- **Building Change Detection** – Compares imagery from two dates to identify changes in built-up areas.
- **Vector Extraction** – Converts detected changes into polygon boundaries.
- **DXF Export** – Exports the results directly to a CAD-compatible DXF file.
- **QGIS Interface** – Provides a simple PyQt interface for selecting layers and adjusting detection parameters.

---

## 🚀 Installation

### From the QGIS Plugin Repository
1. Open QGIS.
2. Go to `Plugins` → `Manage and Install Plugins...`
3. Search for **Building Change to CAD**.
4. Click **Install**.

### From ZIP
1. Download the latest `.zip` file from the [Releases](https://github.com/Abdom7sa/building_change_to_cad/releases) page.
2. Open `Plugins` → `Manage and Install Plugins...` in QGIS.
3. Select **Install from ZIP**.
4. Choose the downloaded ZIP file.

---

## 💻 Usage

1. Open **Building Change to CAD** from the QGIS toolbar or Plugins menu.
2. Select the required SWIR and NIR raster layers.
3. Set the NDBI and change detection thresholds.
4. Set the minimum building area if required.
5. Choose the output DXF file location.
6. Click **Run Detection**.

The plugin processes the input imagery, detects areas of change, converts them into vector features, and exports the results as a DXF file.

---

## 🛠️ Project Structure

```text
building_change_to_cad/
├── __init__.py
├── building_change_to_cad.py
├── building_change_to_cad_dialog.py
├── building_change_to_cad_dialog_base.ui
├── icon.png
├── metadata.txt
└── LICENSE
