import sys
import json
import os
from PyQt5.QtCore import (
    QUrl, Qt, QSize, QTimer
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction,
    QLineEdit, QMessageBox, QStatusBar, QLabel, QWidget, QVBoxLayout
)
from PyQt5.QtGui import QIcon, QMovie, QColor, QPalette
from PyQt5.QtWebEngineWidgets import QWebEngineView
import requests

CONFIG_FILE = 'config.json'

class AppBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        app_name = self.config.get("app_name", "Oponet Dev Browser")
        app_version = self.config.get("app_version", "")
        self.setWindowTitle(f"{app_name} {app_version}".strip())
        self.resize(1080, 720)
        self.set_dark_theme()

        # Set optional icon
        icon_path = self.config.get("iconbitmap", "")
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.webview = QWebEngineView()
        self.layout.addWidget(self.webview)

        # Spinner
        self.spinner_label = QLabel(self)
        self.spinner_label.setFixedSize(48, 48)
        self.spinner_label.setStyleSheet("background: transparent;")
        self.spinner_label.setAttribute(Qt.WA_TranslucentBackground)
        self.spinner_label.setVisible(False)

        self.spinner = QMovie()
        self.spinner.setFileName("")
        self.spinner_label.setMovie(self.spinner)

        self.create_statusbar()

        # Show/hide toolbar based on config
        if self.config.get("nav_enabled", True):
            self.create_toolbar()

        self.webview.loadStarted.connect(self.on_load_started)
        self.webview.loadFinished.connect(self.on_load_finished)
        self.webview.urlChanged.connect(self.update_url_bar)

        self.check_xampp_and_load()

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return {}
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print("Config error:", e)
            return {}

    def set_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(20, 20, 20))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(10, 10, 10))
        palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(100, 100, 255))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setPalette(palette)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.spinner_label.isVisible():
            w = self.webview.width()
            h = self.webview.height()
            self.spinner_label.move(
                self.webview.x() + (w - self.spinner_label.width()) // 2,
                self.webview.y() + (h - self.spinner_label.height()) // 2
            )

    def create_toolbar(self):
        self.toolbar = QToolBar("Navigation")
        self.toolbar.setIconSize(QSize(22, 22))
        self.toolbar.setStyleSheet("""
            QToolBar {
                background: #202020;
                border: none;
            }
            QLineEdit {
                background-color: #121212;
                color: white;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        self.addToolBar(self.toolbar)

        self.back_action = QAction("←", self)
        self.back_action.triggered.connect(self.webview.back)
        self.toolbar.addAction(self.back_action)

        self.forward_action = QAction("→", self)
        self.forward_action.triggered.connect(self.webview.forward)
        self.toolbar.addAction(self.forward_action)

        self.reload_action = QAction("⟳", self)
        self.reload_action.triggered.connect(self.webview.reload)
        self.toolbar.addAction(self.reload_action)

        self.toolbar.addSeparator()

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.toolbar.addWidget(self.url_bar)

        self.toolbar.addSeparator()

        self.clipboard_action = QAction("📋", self)
        self.clipboard_action.triggered.connect(self.copy_url_to_clipboard)
        self.toolbar.addAction(self.clipboard_action)

    def create_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.setStyleSheet("background-color: #111; color: white;")

    def check_xampp_and_load(self):
        url = self.config.get('url', 'http://localhost/')
        self.status.showMessage("Checking XAMPP server...")

        try:
            r = requests.get(url, timeout=3)
            if r.status_code >= 400:
                raise Exception(f"Server error {r.status_code}")

            if self.config.get("check_php", True):
                php_test_url = self.config.get('php_test_url', url + 'phpinfo.php')
                r_php = requests.get(php_test_url, timeout=3)
                if "PHP Version" not in r_php.text:
                    raise Exception("PHP not detected at test URL.")

            self.status.showMessage("XAMPP server OK. Loading app...")
            self.webview.load(QUrl(url))

        except Exception as e:
            self.status.showMessage(f"XAMPP check failed: {e}")
            QMessageBox.critical(self, "Startup Error", str(e))

    def navigate_to_url(self):
        url_text = self.url_bar.text().strip()
        if not url_text.startswith("http"):
            url_text = "http://" + url_text
        self.webview.load(QUrl(url_text))

    def update_url_bar(self, qurl):
        if hasattr(self, 'url_bar'):
            self.url_bar.setText(qurl.toString())
            self.back_action.setEnabled(self.webview.history().canGoBack())
            self.forward_action.setEnabled(self.webview.history().canGoForward())

    def copy_url_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.url_bar.text())
        self.status.showMessage("URL copied to clipboard", 2000)

    def on_load_started(self):
        if self.spinner:
            self.spinner_label.setVisible(True)
            self.spinner.start()
            self.spinner_label.raise_()
            self.resizeEvent(None)
        self.status.showMessage("Loading...")

    def on_load_finished(self, ok):
        if self.spinner:
            self.spinner.stop()
            self.spinner_label.setVisible(False)

        if ok:
            self.status.showMessage("Loaded", 3000)
        else:
            self.status.showMessage("Failed to load", 5000)

def main():
    app = QApplication(sys.argv)
    browser = AppBrowser()
    browser.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
