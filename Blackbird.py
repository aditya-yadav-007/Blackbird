import sys
import os
import socket
import time
import threading
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from PySide6 import QtCore, QtWidgets, QtGui

# default logo path (if you uploaded an image to the environment)
DEFAULT_LOGO = "./BLACKBIRD.png"

# -----------------------------
# Worker threads
# -----------------------------

class PortScannerWorker(QtCore.QThread):
    progress = QtCore.Signal(int, int)  # scanned, total
    found = QtCore.Signal(int)          # open port
    finished = QtCore.Signal(list)

    def __init__(self, target, start=1, end=1024, delay=0.04, timeout=0.4):
        super().__init__()
        self.target = target
        self.start = start
        self.end = end
        self.delay = delay
        self.timeout = timeout
        self._stop = False

    def run(self):
        open_ports = []
        total = (self.end - self.start) + 1
        scanned = 0

        try:
            addr = socket.gethostbyname(self.target)
        except Exception:
            addr = self.target

        for port in range(self.start, self.end + 1):
            if self._stop:
                break
            try:
                s = socket.socket()
                s.settimeout(self.timeout)
                res = s.connect_ex((addr, port))
                s.close()
                if res == 0:
                    open_ports.append(port)
                    self.found.emit(port)
            except Exception:
                pass

            scanned += 1
            self.progress.emit(scanned, total)
            time.sleep(self.delay)

        self.finished.emit(open_ports)

    def stop(self):
        self._stop = True


class DownloaderWorker(QtCore.QThread):
    progress = QtCore.Signal(str)
    assets_found = QtCore.Signal(list)
    finished = QtCore.Signal(str)

    def __init__(self, url, download_assets=False, folder=None):
        super().__init__()
        self.url = url
        self.download_assets = download_assets
        self.folder = folder or "blackbird_download"
        self._stop = False

    def run(self):
        try:
            self.progress.emit(f"GET {self.url}")
            r = requests.get(self.url, timeout=10)
            r.raise_for_status()
            html = r.text
        except Exception as e:
            self.finished.emit(f"ERROR: {e}")
            return

        os.makedirs(self.folder, exist_ok=True)
        index_path = os.path.join(self.folder, "index.html")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html)

        self.progress.emit("Saved index.html")

        soup = BeautifulSoup(html, "lxml")
        assets = []

        # CSS
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if href:
                assets.append(href)

        # JS
        for script in soup.find_all("script"):
            src = script.get("src")
            if src:
                assets.append(src)

        # Images
        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                assets.append(src)

        # Normalize and unique
        normalized = []
        for a in assets:
            full = urljoin(self.url, a)
            if full not in normalized:
                normalized.append(full)

        self.assets_found.emit(normalized)

        if self.download_assets:
            for asset_url in normalized:
                if self._stop:
                    break
                try:
                    self.progress.emit(f"GET {asset_url}")
                    data = requests.get(asset_url, timeout=10).content
                    parsed = urlparse(asset_url)
                    name = parsed.path.lstrip("/") or parsed.netloc
                    name = name.replace("/", "_")
                    path = os.path.join(self.folder, name)
                    with open(path, "wb") as f:
                        f.write(data)
                    self.progress.emit(f"Saved {name}")
                except Exception as e:
                    self.progress.emit(f"Failed {asset_url}: {e}")

        self.finished.emit(f"Done: saved to {os.path.abspath(self.folder)}")

    def stop(self):
        self._stop = True


class SubdomainScannerWorker(QtCore.QThread):
    progress = QtCore.Signal(int, int)  # checked, total
    found = QtCore.Signal(str)          # found subdomain
    finished = QtCore.Signal(list)

    def __init__(self, base_domain, wordlist=None, delay=0.02):
        super().__init__()
        self.base = base_domain
        self.wordlist = wordlist or [
            'www','mail','ftp','test','dev','api','beta','staging','m','web','ns1','ns2','admin'
        ]
        self.delay = delay
        self._stop = False

    def run(self):
        found = []
        total = len(self.wordlist)
        checked = 0

        for sub in self.wordlist:
            if self._stop:
                break
            hostname = f"{sub}.{self.base}"
            try:
                socket.gethostbyname(hostname)
                found.append(hostname)
                self.found.emit(hostname)
            except Exception:
                pass
            checked += 1
            self.progress.emit(checked, total)
            time.sleep(self.delay)

        self.finished.emit(found)

    def stop(self):
        self._stop = True


# -----------------------------
# Main Window (single page)
# -----------------------------

class BlackbirdSinglePageGUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blackbird Lite")
        self.resize(1000, 700)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main = QtWidgets.QVBoxLayout(central)

        # Top banner with optional logo
        banner_layout = QtWidgets.QHBoxLayout()
        main.addLayout(banner_layout)

        if os.path.exists(DEFAULT_LOGO):
            pix = QtGui.QPixmap(DEFAULT_LOGO).scaledToHeight(60, QtCore.Qt.SmoothTransformation)
            logo = QtWidgets.QLabel()
            logo.setPixmap(pix)
            banner_layout.addWidget(logo)

        title = QtWidgets.QLabel("Blackbird Lite")
        title.setStyleSheet("font-size:18px; font-weight:700; padding:8px;")
        banner_layout.addWidget(title)
        banner_layout.addStretch()

        desc = QtWidgets.QLabel("Port scan • Webpage downloader • Subdomain scanner")
        desc.setStyleSheet("color:gray")
        banner_layout.addWidget(desc)

        # Controls area: three group boxes in one row
        controls = QtWidgets.QHBoxLayout()
        main.addLayout(controls)

        # ------------------ Port Scanner Box ------------------
        box_scan = QtWidgets.QGroupBox("Port Scanner")
        box_scan.setMinimumWidth(300)
        controls.addWidget(box_scan)
        s_layout = QtWidgets.QVBoxLayout(box_scan)

        self.scan_target = QtWidgets.QLineEdit()
        self.scan_target.setPlaceholderText("Target (example.com or 192.168.1.10)")
        s_layout.addWidget(self.scan_target)

        h = QtWidgets.QHBoxLayout()
        s_layout.addLayout(h)
        self.scan_btn = QtWidgets.QPushButton("Start")
        self.scan_btn.clicked.connect(self.start_scan)
        h.addWidget(self.scan_btn)
        self.scan_stop = QtWidgets.QPushButton("Stop")
        self.scan_stop.clicked.connect(self.stop_scan)
        self.scan_stop.setEnabled(False)
        h.addWidget(self.scan_stop)

        self.scan_progress = QtWidgets.QProgressBar()
        s_layout.addWidget(self.scan_progress)
        self.scan_results = QtWidgets.QListWidget()
        s_layout.addWidget(self.scan_results)

        # ------------------ Downloader Box ------------------
        box_down = QtWidgets.QGroupBox("Webpage Downloader")
        box_down.setMinimumWidth(320)
        controls.addWidget(box_down)
        d_layout = QtWidgets.QVBoxLayout(box_down)

        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        d_layout.addWidget(self.url_input)

        self.assets_checkbox = QtWidgets.QCheckBox("Download assets (CSS/JS/Images)")
        d_layout.addWidget(self.assets_checkbox)

        folder_h = QtWidgets.QHBoxLayout()
        d_layout.addLayout(folder_h)
        self.folder_input = QtWidgets.QLineEdit("blackbird_download")
        folder_h.addWidget(self.folder_input)
        self.folder_btn = QtWidgets.QPushButton("Browse")
        self.folder_btn.clicked.connect(self.browse_folder)
        folder_h.addWidget(self.folder_btn)

        h2 = QtWidgets.QHBoxLayout()
        d_layout.addLayout(h2)
        self.down_btn = QtWidgets.QPushButton("Download")
        self.down_btn.clicked.connect(self.start_download)
        h2.addWidget(self.down_btn)
        self.down_stop = QtWidgets.QPushButton("Stop")
        self.down_stop.clicked.connect(self.stop_download)
        self.down_stop.setEnabled(False)
        h2.addWidget(self.down_stop)

        self.assets_list = QtWidgets.QListWidget()
        d_layout.addWidget(self.assets_list)

        # ------------------ Subdomain Box ------------------
        box_sub = QtWidgets.QGroupBox("Subdomain Scanner")
        box_sub.setMinimumWidth(300)
        controls.addWidget(box_sub)
        sub_layout = QtWidgets.QVBoxLayout(box_sub)

        self.base_domain = QtWidgets.QLineEdit()
        self.base_domain.setPlaceholderText("example.com")
        sub_layout.addWidget(self.base_domain)

        wl_h = QtWidgets.QHBoxLayout()
        sub_layout.addLayout(wl_h)
        self.load_wordlist_btn = QtWidgets.QPushButton("Load wordlist")
        self.load_wordlist_btn.clicked.connect(self.load_wordlist)
        wl_h.addWidget(self.load_wordlist_btn)
        self.wordlist_label = QtWidgets.QLabel("default small wordlist")
        wl_h.addWidget(self.wordlist_label)

        h3 = QtWidgets.QHBoxLayout()
        sub_layout.addLayout(h3)
        self.sub_start = QtWidgets.QPushButton("Start")
        self.sub_start.clicked.connect(self.start_subscan)
        h3.addWidget(self.sub_start)
        self.sub_stop = QtWidgets.QPushButton("Stop")
        self.sub_stop.clicked.connect(self.stop_subscan)
        self.sub_stop.setEnabled(False)
        h3.addWidget(self.sub_stop)

        self.sub_progress = QtWidgets.QProgressBar()
        sub_layout.addWidget(self.sub_progress)
        self.sub_results = QtWidgets.QListWidget()
        sub_layout.addWidget(self.sub_results)

        # Log area
        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        main.addWidget(self.log, stretch=1)

        # Status bar
        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)

        # Workers
        self.scanner_worker = None
        self.downloader_worker = None
        self.sub_worker = None
        self.custom_wordlist = None

    # -----------------------------
    # Port scanner methods
    # -----------------------------
    def start_scan(self):
        target = self.scan_target.text().strip()
        if not target:
            self._log("Enter a target to scan")
            return
        self.scan_results.clear()
        self.scan_progress.setValue(0)
        self.scan_btn.setEnabled(False)
        self.scan_stop.setEnabled(True)
        self._log(f"Starting port scan on {target} (1-1024)")

        self.scanner_worker = PortScannerWorker(target, start=1, end=1024, delay=0.02, timeout=0.3)
        self.scanner_worker.progress.connect(self._on_scan_progress)
        self.scanner_worker.found.connect(self._on_scan_found)
        self.scanner_worker.finished.connect(self._on_scan_finished)
        self.scanner_worker.start()

    def stop_scan(self):
        if self.scanner_worker:
            self.scanner_worker.stop()
            self._log("Stopping scan...")
            self.scan_stop.setEnabled(False)

    def _on_scan_progress(self, scanned, total):
        value = int((scanned / total) * 100)
        self.scan_progress.setValue(value)

    def _on_scan_found(self, port):
        self.scan_results.addItem(f"Port {port} open")
        self._log(f"Found open port: {port}")

    def _on_scan_finished(self, open_ports):
        self._log(f"Scan finished. {len(open_ports)} open ports found.")
        self.scan_btn.setEnabled(True)
        self.scan_stop.setEnabled(False)

    # -----------------------------
    # Downloader methods
    # -----------------------------
    def browse_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose folder", os.getcwd())
        if folder:
            self.folder_input.setText(folder)

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            self._log("Enter a URL to download")
            return
        download_assets = self.assets_checkbox.isChecked()
        folder = self.folder_input.text().strip() or "blackbird_download"

        self.assets_list.clear()
        self.down_btn.setEnabled(False)
        self.down_stop.setEnabled(True)
        self._log(f"Starting download: {url}")

        self.downloader_worker = DownloaderWorker(url, download_assets=download_assets, folder=folder)
        self.downloader_worker.progress.connect(lambda s: self._log(s))
        self.downloader_worker.assets_found.connect(self._on_assets_found)
        self.downloader_worker.finished.connect(self._on_download_finished)
        self.downloader_worker.start()

    def stop_download(self):
        if self.downloader_worker:
            self.downloader_worker.stop()
            self._log("Stopping download...")
            self.down_stop.setEnabled(False)

    def _on_assets_found(self, assets):
        self._log(f"Assets found: {len(assets)}")
        for a in assets:
            self.assets_list.addItem(a)

    def _on_download_finished(self, msg):
        self._log(msg)
        self.down_btn.setEnabled(True)
        self.down_stop.setEnabled(False)

    # -----------------------------
    # Subdomain methods
    # -----------------------------
    def load_wordlist(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open wordlist file", os.getcwd(), "Text files (*.txt);;All files (*)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [l.strip() for l in f if l.strip()]
                self.custom_wordlist = lines
                self.wordlist_label.setText(f"Loaded: {os.path.basename(path)} ({len(lines)} entries)")
                self._log(f"Loaded wordlist {path} ({len(lines)} entries)")
            except Exception as e:
                self._log(f"Failed to load wordlist: {e}")

    def start_subscan(self):
        base = self.base_domain.text().strip()
        if not base:
            self._log("Enter a base domain (example.com)")
            return
        wordlist = self.custom_wordlist or None
        self.sub_results.clear()
        self.sub_progress.setValue(0)
        self.sub_start.setEnabled(False)
        self.sub_stop.setEnabled(True)
        self._log(f"Starting subdomain scan on {base}")

        self.sub_worker = SubdomainScannerWorker(base, wordlist=wordlist)
        self.sub_worker.progress.connect(self._on_sub_progress)
        self.sub_worker.found.connect(self._on_sub_found)
        self.sub_worker.finished.connect(self._on_sub_finished)
        self.sub_worker.start()

    def stop_subscan(self):
        if self.sub_worker:
            self.sub_worker.stop()
            self._log("Stopping subdomain scan...")
            self.sub_stop.setEnabled(False)

    def _on_sub_progress(self, checked, total):
        value = int((checked / total) * 100) if total else 0
        self.sub_progress.setValue(value)

    def _on_sub_found(self, host):
        self.sub_results.addItem(host)
        self._log(f"Found subdomain: {host}")

    def _on_sub_finished(self, found):
        self._log(f"Subdomain scan finished. {len(found)} found.")
        self.sub_start.setEnabled(True)
        self.sub_stop.setEnabled(False)

    # -----------------------------
    # Misc
    # -----------------------------
    def _log(self, msg):
        ts = QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.log.append(f"[{ts}] {msg}")
        self.status.showMessage(msg, 5000)


# -----------------------------
# Entry
# -----------------------------

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = BlackbirdSinglePageGUI()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
