import os
import sys
# Ensure the script directory is in the search path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from datetime import datetime

import pandas as pd
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QTextEdit,
)

from transfer_features import (
    ensure_dir,
    extract_features_for_sweep,
    load_transfer_data,
    plot_transfer_summary,
    split_sweeps_by_turning_point,
)


class DropListWidget(QListWidget):
    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            return
        paths = [u.toLocalFile() for u in event.mimeData().urls()]
        self.files_dropped.emit(paths)


class TransferApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transfer Curve Analyzer")
        self.resize(900, 600)

        self.file_list = DropListWidget()
        self.file_list.files_dropped.connect(self.add_paths)

        self.output_label = QLabel("Output: (not set, will prompt)")
        self.output_dir = None

        self.device_type_combo = QComboBox()
        self.device_type_combo.addItems(["auto", "n", "p"])

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        add_files_btn = QPushButton("Add Files")
        add_files_btn.clicked.connect(self.add_files)

        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.add_folder)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.file_list.clear)

        choose_output_btn = QPushButton("Choose Output")
        choose_output_btn.clicked.connect(self.choose_output_dir)

        run_btn = QPushButton("Run")
        run_btn.clicked.connect(self.run_processing)

        top_row = QHBoxLayout()
        top_row.addWidget(add_files_btn)
        top_row.addWidget(add_folder_btn)
        top_row.addWidget(clear_btn)
        top_row.addStretch(1)
        top_row.addWidget(QLabel("Device type:"))
        top_row.addWidget(self.device_type_combo)

        output_row = QHBoxLayout()
        output_row.addWidget(self.output_label)
        output_row.addStretch(1)
        output_row.addWidget(choose_output_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_row)
        main_layout.addWidget(QLabel("Drop CSV files or folders below:"))
        main_layout.addWidget(self.file_list, 3)
        main_layout.addLayout(output_row)
        main_layout.addWidget(run_btn)
        main_layout.addWidget(QLabel("Log:"))
        main_layout.addWidget(self.log_box, 2)
        self.setLayout(main_layout)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f"[{timestamp}] {message}")

    def add_paths(self, paths):
        files = self._collect_csv_files(paths)
        if not files:
            self.log("No CSV files found.")
            return
        existing = set(self._current_files())
        for f in files:
            if f not in existing:
                self.file_list.addItem(f)
        self.log(f"Added {len(files)} files.")

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select CSV files", "", "CSV Files (*.csv)")
        if paths:
            self.add_paths(paths)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder")
        if folder:
            self.add_paths([folder])

    def choose_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.output_dir = folder
            self.output_label.setText(f"Output: {folder}")

    def _current_files(self):
        return [self.file_list.item(i).text() for i in range(self.file_list.count())]

    def _collect_csv_files(self, paths):
        results = []
        for p in paths:
            if os.path.isdir(p):
                for root, _, files in os.walk(p):
                    for name in files:
                        if name.lower().endswith(".csv") and name.lower() != "results.csv":
                            results.append(os.path.join(root, name))
            elif os.path.isfile(p) and p.lower().endswith(".csv") and os.path.basename(p).lower() != "results.csv":
                results.append(p)
        return results

    def _ensure_output_dir(self):
        if self.output_dir:
            ensure_dir(self.output_dir)
            return self.output_dir
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if not folder:
            return None
        self.output_dir = folder
        self.output_label.setText(f"Output: {folder}")
        ensure_dir(folder)
        return folder

    def run_processing(self):
        files = self._current_files()
        if not files:
            QMessageBox.warning(self, "No files", "Please add CSV files or folders first.")
            return

        output_dir = self._ensure_output_dir()
        if not output_dir:
            QMessageBox.warning(self, "No output", "Please choose an output folder.")
            return

        device_type = self.device_type_combo.currentText()
        results = []

        for path in files:
            self.log(f"Processing: {path}")
            vg, idc = load_transfer_data(path)
            if vg is None or idc is None:
                self.log(f"  Skipped (invalid data): {path}")
                continue

            base_name = os.path.splitext(os.path.basename(path))[0]
            sweeps = split_sweeps_by_turning_point(vg, idc)

            for sweep_label, vg_seg, id_seg in sweeps:
                if len(vg_seg) < 5:
                    self.log(f"  Skipped (too few points): {base_name} {sweep_label}")
                    continue

                features = extract_features_for_sweep(vg_seg, id_seg, device_type)
                title = base_name
                output_name = f"{base_name}_{sweep_label}_transfer.jpg"
                output_path = os.path.join(output_dir, output_name)

                plot_transfer_summary(
                    vg_seg,
                    id_seg,
                    features["ss_fit"],
                    features["gm"],
                    features["vth_info"],
                    features["onoff"],
                    features["max_id"],
                    features["max_gm"],
                    features["device_type"],
                    title,
                    output_path,
                )

                results.append(
                    {
                        "file": base_name,
                        "sweep": sweep_label,
                        "device_type": features["device_type"],
                        "Vth": features["vth_info"]["Vth"],
                        "onoff_ratio": features["onoff"],
                        "SS": features["ss"],
                        "max_Id": features["max_id"],
                        "max_gm": features["max_gm"],
                        "plot": output_name,
                    }
                )

        if results:
            out_csv = os.path.join(output_dir, "transfer_results.csv")
            pd.DataFrame(results).to_csv(out_csv, index=False, encoding="utf-8-sig")
            self.log(f"Saved results: {out_csv}")
        else:
            self.log("No results produced.")

        QMessageBox.information(self, "Done", "Processing completed.")


def main():
    app = QApplication(sys.argv)
    window = TransferApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
