import sys
import os
import struct
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QMessageBox, QLineEdit, QHBoxLayout
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt
import win32api
import win32con

class IconChanger(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MiniusSoft Icon Changer | EXE Icon Editor")

        self.setFixedSize(460, 240)
        self.init_ui()
        self.set_dark_theme()

    def init_ui(self):
        layout = QVBoxLayout()

        # Heading Label
        heading = QLabel("MiniusSoft LTD - EXE Icon Changer")
        heading.setFont(QFont("Segoe UI", 12, QFont.Bold))
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)

        # EXE file picker
        self.exe_path_edit = QLineEdit()
        self.exe_path_edit.setPlaceholderText("Select EXE file...")
        self.exe_browse_btn = QPushButton("Browse EXE")
        self.exe_browse_btn.clicked.connect(self.browse_exe)
        exe_layout = QHBoxLayout()
        exe_layout.addWidget(self.exe_path_edit)
        exe_layout.addWidget(self.exe_browse_btn)
        layout.addLayout(exe_layout)

        # ICO file picker
        self.ico_path_edit = QLineEdit()
        self.ico_path_edit.setPlaceholderText("Select ICO file...")
        self.ico_browse_btn = QPushButton("Browse ICO")
        self.ico_browse_btn.clicked.connect(self.browse_ico)
        ico_layout = QHBoxLayout()
        ico_layout.addWidget(self.ico_path_edit)
        ico_layout.addWidget(self.ico_browse_btn)
        layout.addLayout(ico_layout)

        # Change icon button
        self.change_btn = QPushButton("Change Icon Now")
        self.change_btn.clicked.connect(self.change_icon)
        layout.addWidget(self.change_btn)

        # Footer / Copyright
        footer = QLabel("© 2025 MiniusSoft Ltd - All rights reserved.")
        footer.setFont(QFont("Segoe UI", 8))
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        self.setLayout(layout)

    def set_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(40, 40, 40))
        dark_palette.setColor(QPalette.AlternateBase, QColor(60, 60, 60))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setPalette(dark_palette)

    def browse_exe(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select EXE file", "", "Executable Files (*.exe)")
        if path:
            self.exe_path_edit.setText(path)

    def browse_ico(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select ICO file", "", "Icon Files (*.ico)")
        if path:
            self.ico_path_edit.setText(path)

    def change_icon(self):
        exe_path = self.exe_path_edit.text().strip()
        ico_path = self.ico_path_edit.text().strip()

        if not os.path.isfile(exe_path):
            QMessageBox.warning(self, "Error", "Invalid EXE file path.")
            return
        if not os.path.isfile(ico_path):
            QMessageBox.warning(self, "Error", "Invalid ICO file path.")
            return

        try:
            self.update_icon(exe_path, ico_path)
            QMessageBox.information(self, "Success", "Icon changed successfully!\nYou might need to clear icon cache or restart Explorer.")
        except Exception as e:
            QMessageBox.critical(self, "Failed", f"Could not change icon:\n{e}")

    def update_icon(self, exe_path, ico_path):
        with open(ico_path, 'rb') as f:
            icon_data = f.read()

        id_count = struct.unpack_from('<H', icon_data, 4)[0]
        required_size = 6 + (16 * id_count)
        if required_size > len(icon_data):
            raise ValueError(f"ICO file too small or corrupted. Expected {required_size} bytes, got {len(icon_data)}")

        entries = []
        for i in range(id_count):
            offset = 6 + 16 * i
            entry = struct.unpack_from('<BBBBHHII', icon_data, offset)
            width, height, color_count, reserved, planes, bit_count, size, icon_offset = entry
            entries.append({
                "width": width,
                "height": height,
                "color_count": color_count,
                "reserved": reserved,
                "planes": planes,
                "bit_count": bit_count,
                "size": size,
                "offset": icon_offset
            })

        hUpdate = win32api.BeginUpdateResource(exe_path, False)

        grp_icon_dir = bytearray(icon_data[:6])
        struct.pack_into('<H', grp_icon_dir, 4, id_count)

        grp_entries = bytearray()
        for i, entry in enumerate(entries):
            grp_entries.extend(struct.pack(
                '<BBBBHHIH',
                entry["width"] if entry["width"] != 0 else 256,
                entry["height"] if entry["height"] != 0 else 256,
                entry["color_count"],
                entry["reserved"],
                entry["planes"],
                entry["bit_count"],
                entry["size"],
                i + 1
            ))

        group_icon_data = grp_icon_dir + grp_entries

        win32api.UpdateResource(hUpdate, win32con.RT_GROUP_ICON, 1, group_icon_data)

        for i, entry in enumerate(entries):
            rt_icon_data = icon_data[entry["offset"]:entry["offset"] + entry["size"]]
            win32api.UpdateResource(hUpdate, win32con.RT_ICON, i + 1, rt_icon_data)

        win32api.EndUpdateResource(hUpdate, False)

def main():
    app = QApplication(sys.argv)
    window = IconChanger()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
