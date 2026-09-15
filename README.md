# Building Change Detection to CAD (QGIS Plugin)

An automated QGIS Python plugin designed for urban change detection using multi-temporal satellite imagery. It computes NDBI spectral differencing, extracts changed building structures, and directly exports vectors into AutoCAD DXF format.

## Features
- **Spectral Index Calculation:** Computes NDBI across Time 1 and Time 2 rasters.
- **Noise Filtering:** Applies area-based thresholding to eliminate minor artifacts.
- **Geometry Smoothing:** Refines vector polygons for clean CAD integration.
- **Direct DXF Export:** Saves results directly as DXF files without intermediate manual conversion.

## Installation
1. Download or clone this repository.
2. Copy the plugin folder to your QGIS profiles directory:
   `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
3. Restart QGIS and enable **Building Change to CAD** from the **Plugin Manager**.

## Usage
1. Open the plugin from the QGIS toolbar.
2. Select SWIR and NIR bands for both Time 1 and Time 2.
3. Set the NDBI Threshold Difference and Minimum Building Area (m²).
4. Specify the output path for the `.dxf` file and click **Run Detection**.

## Author
Abdalrhman Musa
