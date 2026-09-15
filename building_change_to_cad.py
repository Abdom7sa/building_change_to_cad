"""
Building Change Detection & DXF Exporter
---------------------------------------
Author: Abdalrhman Musa
Description: A QGIS plugin that automates urban building change detection 
             using dual-date NDBI spectral differencing and outputs smoothed 
             vector boundaries to AutoCAD DXF format.
"""

import os
import processing
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QAction, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QDoubleSpinBox, QSpinBox, QPushButton, 
    QFileDialog, QMessageBox
)
from qgis.core import (
    QgsProject, 
    QgsDxfExport, 
    QgsMessageLog, 
    Qgis
)


class BuildingChangeDialog(QDialog):
    """Custom GUI for selecting multi-temporal rasters and parameters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Building Change Detection to CAD")
        self.resize(440, 360)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # --- Section 1: Input Rasters ---
        main_layout.addWidget(QLabel("<b>1. Select Input Spectral Bands</b>"))
        
        # Time 1 selection
        grid_t1 = QHBoxLayout()
        self.combo_swir1 = QComboBox()
        self.combo_nir1 = QComboBox()
        grid_t1.addWidget(QLabel("SWIR (T1):"))
        grid_t1.addWidget(self.combo_swir1)
        grid_t1.addWidget(QLabel("NIR (T1):"))
        grid_t1.addWidget(self.combo_nir1)
        main_layout.addLayout(grid_t1)

        # Time 2 selection
        grid_t2 = QHBoxLayout()
        self.combo_swir2 = QComboBox()
        self.combo_nir2 = QComboBox()
        grid_t2.addWidget(QLabel("SWIR (T2):"))
        grid_t2.addWidget(self.combo_swir2)
        grid_t2.addWidget(QLabel("NIR (T2):"))
        grid_t2.addWidget(self.combo_nir2)
        main_layout.addLayout(grid_t2)

        # --- Section 2: Thresholds & Filtering ---
        main_layout.addWidget(QLabel("<b>2. Detection Parameters</b>"))
        
        params_layout = QHBoxLayout()
        
        self.spin_threshold = QDoubleSpinBox()
        self.spin_threshold.setRange(-1.0, 1.0)
        self.spin_threshold.setSingleStep(0.05)
        self.spin_threshold.setValue(0.20)
        
        self.spin_min_area = QSpinBox()
        self.spin_min_area.setRange(1, 100000)
        self.spin_min_area.setValue(50)  # Default 50 m^2 to exclude noise

        params_layout.addWidget(QLabel("NDBI Threshold:"))
        params_layout.addWidget(self.spin_threshold)
        params_layout.addWidget(QLabel("Min Area (m²):"))
        params_layout.addWidget(self.spin_min_area)
        main_layout.addLayout(params_layout)

        # --- Section 3: Output CAD File ---
        main_layout.addWidget(QLabel("<b>3. Export Location</b>"))
        
        out_layout = QHBoxLayout()
        self.combo_output_path = QComboBox()
        self.combo_output_path.setEditable(True)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._on_browse_clicked)
        
        out_layout.addWidget(self.combo_output_path)
        out_layout.addWidget(btn_browse)
        main_layout.addLayout(out_layout)

        # --- Action Buttons ---
        btn_layout = QHBoxLayout()
        self.btn_run = QPushButton("Run Detection")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_run.setDefault(True)

        self.btn_run.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_run)
        btn_layout.addWidget(self.btn_cancel)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def _on_browse_clicked(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CAD File", "", "AutoCAD DXF File (*.dxf)"
        )
        if file_path:
            self.combo_output_path.setCurrentText(file_path)


class BuildingChangeToCAD:
    """Main QGIS Plugin Execution Class."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = None
        self.dlg = None

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.action = QAction(
            QIcon(icon_path), 
            'Building Change to CAD', 
            self.iface.mainWindow()
        )
        self.action.triggered.connect(self.run)
        
        self.iface.addPluginToMenu('&Building Change Tools', self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removePluginMenu('&Building Change Tools', self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        self.dlg = BuildingChangeDialog(self.iface.mainWindow())
        self._populate_rasters()

        if self.dlg.exec_():
            self._execute_pipeline()

    def _populate_rasters(self):
        """Fetch active raster layers from current project canvas."""
        project_layers = QgsProject.instance().mapLayers().values()
        raster_names = [lyr.name() for lyr in project_layers if lyr.type() == lyr.RasterLayer]

        target_combos = [
            self.dlg.combo_swir1, self.dlg.combo_nir1,
            self.dlg.combo_swir2, self.dlg.combo_nir2
        ]

        for combo in target_combos:
            combo.clear()
            combo.addItems(raster_names)

    def _execute_pipeline(self):
        """Executes full change detection workflow: NDBI -> Raster Calc -> Polygonize -> DXF Export."""
        try:
            # 1. Parse inputs from dialog
            swir1_name = self.dlg.combo_swir1.currentText()
            nir1_name = self.dlg.combo_nir1.currentText()
            swir2_name = self.dlg.combo_swir2.currentText()
            nir2_name = self.dlg.combo_nir2.currentText()

            threshold_val = self.dlg.spin_threshold.value()
            min_area_val = self.dlg.spin_min_area.value()
            dxf_target_path = self.dlg.combo_output_path.currentText().strip()

            if not dxf_target_path:
                QMessageBox.warning(None, "Missing Input", "Please select a valid output path for DXF export.")
                return

            # 2. Retrieve layer objects
            layer_names = [swir1_name, nir1_name, swir2_name, nir2_name]
            loaded_layers = {}
            for name in layer_names:
                match = QgsProject.instance().mapLayersByName(name)
                if not match:
                    QMessageBox.critical(None, "Layer Missing", f"Could not find layer '{name}' in project.")
                    return
                loaded_layers[name] = match[0]

            # 3. Extract raster spatial metadata
            ref_layer = loaded_layers[swir1_name]
            crs = ref_layer.crs()
            ext = ref_layer.extent()
            extent_str = f"{ext.xMinimum()},{ext.xMaximum()},{ext.yMinimum()},{ext.yMaximum()}"

            cell_size = ref_layer.rasterUnitsPerPixelX()
            if cell_size <= 0:
                cell_size = 10.0  # Fallback resolution for synthetic rasters

            layer_list = list(loaded_layers.values())

            # 4. Raster calculation (NDBI logic & Change detection)
            # NDBI = (SWIR - NIR) / (SWIR + NIR)
            expr_ndbi1 = f'("{swir1_name}@1" - "{nir1_name}@1") / ("{swir1_name}@1" + "{nir1_name}@1")'
            expr_ndbi2 = f'("{swir2_name}@1" - "{nir2_name}@1") / ("{swir2_name}@1" + "{nir2_name}@1")'
            expr_diff = f'({expr_ndbi2}) - ({expr_ndbi1}) > {threshold_val}'

            diff_raster = processing.run("qgis:rastercalculator", {
                'EXPRESSION': expr_diff,
                'LAYERS': layer_list,
                'CELLSIZE': cell_size,
                'EXTENT': extent_str,
                'CRS': crs,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })['OUTPUT']

            # 5. Vectorize raster changes
            raw_polygons = processing.run("gdal:polygonize", {
                'INPUT': diff_raster,
                'BAND': 1,
                'FIELD': 'DN',
                'EIGHT_CONNECTEDNESS': False,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })['OUTPUT']

            # 6. Filter out background pixels and small area artifacts
            filtered_polygons = processing.run("native:extractbyexpression", {
                'INPUT': raw_polygons,
                'EXPRESSION': f'"DN" = 1 AND $area >= {min_area_val}',
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })['OUTPUT']

            # 7. Geometry smoothing for CAD aesthetic
            smoothed_polygons = processing.run("native:smoothgeometry", {
                'INPUT': filtered_polygons,
                'ITERATIONS': 2,
                'OFFSET': 0.25,
                'MAX_ANGLE': 180,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })['OUTPUT']

            # 8. Export result layer to DXF
            dxf_exporter = QgsDxfExport()
            dxf_exporter.setCrs(smoothed_polygons.crs())
            dxf_exporter.setSymbologyScale(1000)
            dxf_exporter.setSymbologyMode(QgsDxfExport.NoSymbology)

            dxf_layer = QgsDxfExport.DxfLayer(smoothed_polygons)
            dxf_exporter.addLayers([dxf_layer])

            with open(dxf_target_path, 'wb') as stream:
                dxf_exporter.writeGroup(stream)

            # 9. Feedback to user
            self.iface.messageBar().pushMessage(
                "Success", f"CAD file successfully generated at {dxf_target_path}", 
                level=Qgis.Success, duration=6
            )
            QMessageBox.information(
                None, "Process Complete", 
                f"Building change detection finished!\n\nExported file:\n{dxf_target_path}"
            )

        except Exception as err:
            QgsMessageLog.logMessage(str(err), 'BuildingChangeToCAD', level=Qgis.Critical)
            QMessageBox.critical(
                None, "Pipeline Error", 
                f"An error occurred during execution:\n\n{str(err)}"
            )