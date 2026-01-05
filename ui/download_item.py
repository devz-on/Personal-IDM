import asyncio
import time
from threading import Thread

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QFrame,
)
from PySide6.QtCore import QObject, Signal

from core.downloader import Downloader


# -------------------- Signals --------------------

class ItemSignals(QObject):
    progress = Signal(int, int)
    stream = Signal(int, int, int, int)  # id, downloaded, start, end
    finished = Signal()
    error = Signal(str)
    status = Signal(str)


# -------------------- Helpers --------------------

def human(size: float) -> str:
    if size <= 0:
        return "0 B"
    for u in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f} {u}"
        size /= 1024
    return f"{size:.2f} TB"


def fmt_time(sec: float) -> str:
    if sec <= 0 or sec == float("inf"):
        return "∞"
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


# -------------------- Download Item --------------------

class DownloadItem(QWidget):
    def __init__(self, url: str, output_path: str, connections: int = 8):
        super().__init__()

        self.url = url
        self.output_path = output_path
        self.connections = connections

        self.signals = ItemSignals()
        self.signals.progress.connect(self.on_progress)
        self.signals.stream.connect(self.on_stream)
        self.signals.finished.connect(self.on_finished)
        self.signals.error.connect(self.on_error)
        self.signals.status.connect(self.on_status)

        self.downloader = None

        # global speed
        self._last_time = time.time()
        self._last_bytes = 0
        self._speed = 0.0

        # per-stream tracking
        self.stream_bytes = {}
        self.stream_ranges = {}

        self._build_ui()

    # -------------------- UI --------------------

    def _build_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(8, 8, 8, 8)

        name = self.output_path.replace("\\", "/").split("/")[-1]
        self.file_label = QLabel(name)
        self.file_label.setStyleSheet("font-weight: bold;")

        self.main_bar = QProgressBar()
        self.main_bar.setValue(0)

        self.details = QLabel("Speed: 0 KB/s | ETA: ∞ | Streams: 0")
        self.details.setStyleSheet("color: gray; font-size: 11px;")

        self.status = QLabel("Waiting")
        self.status.setStyleSheet("color: #aaa; font-size: 11px;")

        root.addWidget(self.file_label)
        root.addWidget(self.main_bar)
        root.addWidget(self.details)
        root.addWidget(self.status)

        # ---------- Stream list ----------
        self.stream_labels = {}
        stream_box = QVBoxLayout()
        stream_box.setSpacing(2)

        for i in range(self.connections):
            lbl = QLabel(f"Stream {i+1}: idle")
            lbl.setStyleSheet("font-size: 10px; color: #bbb;")
            self.stream_labels[i] = lbl
            stream_box.addWidget(lbl)

        frame = QFrame()
        frame.setLayout(stream_box)
        frame.setFrameShape(QFrame.StyledPanel)

        root.addWidget(frame)

        # ---------- Buttons ----------
        btns = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setEnabled(False)

        self.start_btn.clicked.connect(self.start)
        self.pause_btn.clicked.connect(self.pause)

        btns.addWidget(self.start_btn)
        btns.addWidget(self.pause_btn)
        btns.addStretch()

        root.addLayout(btns)
        self.setLayout(root)

    # -------------------- Actions --------------------

    def start(self):
        if self.downloader is None:
            self.downloader = Downloader(
                url=self.url,
                output_path=self.output_path,
                connections=self.connections,
                progress_callback=self.progress_callback,
                stream_callback=self.stream_callback,
            )

        self._last_time = time.time()
        self._last_bytes = 0
        self.stream_bytes.clear()
        self.stream_ranges.clear()

        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.signals.status.emit("Downloading...")

        Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            asyncio.run(self.downloader.start())
            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(str(e))

    def pause(self):
        if self.downloader:
            self.downloader.stop()
            self.signals.status.emit("Paused")
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)

    # -------------------- Callbacks --------------------

    def progress_callback(self, downloaded, total):
        self.signals.progress.emit(downloaded, total)

    def stream_callback(self, stream_id, downloaded, start, end):
        self.signals.stream.emit(stream_id, downloaded, start, end)

    def on_progress(self, downloaded, total):
        now = time.time()
        dt = now - self._last_time
        db = downloaded - self._last_bytes

        if dt > 0:
            self._speed = db / dt

        self._last_time = now
        self._last_bytes = downloaded

        if total > 0:
            pct = int((downloaded / total) * 100)
            self.main_bar.setValue(pct)
            eta = (total - downloaded) / self._speed if self._speed > 0 else float("inf")
        else:
            eta = float("inf")

        self.details.setText(
            f"Speed: {human(self._speed)}/s | ETA: {fmt_time(eta)} | Streams: {len(self.stream_bytes)}"
        )

    def on_stream(self, stream_id, downloaded, start, end):
        self.stream_bytes[stream_id] = downloaded
        self.stream_ranges[stream_id] = (start, end)

        total = end - start + 1
        pct = (downloaded / total) * 100 if total > 0 else 0

        self.stream_labels[stream_id].setText(
            f"Stream {stream_id+1}: "
            f"{human(downloaded)} / {human(total)} "
            f"({pct:.1f}%)"
        )

    def on_finished(self):
        self.main_bar.setValue(100)
        self.status.setText("Completed ✔")
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)

    def on_error(self, msg):
        self.status.setText(f"Error: {msg}")
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

    def on_status(self, text):
        self.status.setText(text)
