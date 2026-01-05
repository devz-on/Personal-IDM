import sys
import os
from urllib.parse import urlparse, unquote

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QScrollArea,
    QMessageBox,
)
from PySide6.QtCore import Qt

from ui.download_item import DownloadItem


DEFAULT_DOWNLOAD_DIR = "H:/DM/"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Devz Download Manager")
        self.setMinimumSize(750, 420)

        os.makedirs(DEFAULT_DOWNLOAD_DIR, exist_ok=True)

        self._build_ui()

    # -------------------- UI --------------------

    def _build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout()

        # -------- Add Download Section --------
        add_layout = QHBoxLayout()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste download URL here...")

        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText(f"Auto (saved to {DEFAULT_DOWNLOAD_DIR})")

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_download)

        add_layout.addWidget(self.url_input, 4)
        add_layout.addWidget(self.file_input, 3)
        add_layout.addWidget(browse_btn)
        add_layout.addWidget(add_btn)

        main_layout.addLayout(add_layout)

        # -------- Download List --------
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout()
        self.list_layout.setAlignment(Qt.AlignTop)

        self.list_container.setLayout(self.list_layout)
        self.scroll.setWidget(self.list_container)

        main_layout.addWidget(self.scroll)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

    # -------------------- Helpers --------------------

    def extract_filename(self, url: str) -> str:
        parsed = urlparse(url)
        name = os.path.basename(parsed.path)
        name = unquote(name)

        if not name or "." not in name:
            return "download.bin"

        return name

    # -------------------- Actions --------------------

    def browse_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            DEFAULT_DOWNLOAD_DIR,
        )
        if path:
            self.file_input.setText(path)

    def add_download(self):
        url = self.url_input.text().strip()
        manual_path = self.file_input.text().strip()

        if not url:
            QMessageBox.warning(self, "Error", "Please enter a download URL")
            return

        # Auto filename if user didn't choose
        if manual_path:
            output_path = manual_path
        else:
            filename = self.extract_filename(url)
            output_path = os.path.join(DEFAULT_DOWNLOAD_DIR, filename)

        item = DownloadItem(url, output_path)
        self.list_layout.addWidget(item)

        self.url_input.clear()
        self.file_input.clear()


# -------------------- Entry --------------------

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
