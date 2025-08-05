import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QLineEdit, QRadioButton, QComboBox, QPushButton,
    QCheckBox, QProgressBar, QLabel
)
from PySide6.QtCore import Qt, QObject, Signal, QThread

# 1. Create a new class named `Worker` that inherits from `QObject`.
class Worker(QObject):
    """
    Handles long-running tasks in a separate thread.
    """
    # 2. Define custom signals for communication.
    info_ready = Signal(dict)
    progress = Signal(int)
    finished = Signal(dict)
    error = Signal(str)

class VidAudDownload(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VidAudDownload")
        self.resize(800, 600)

        # --- UI Setup (from Step 2) ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste video or playlist URL here")
        main_layout.addWidget(self.url_input)

        media_type_layout = QHBoxLayout()
        self.video_radio = QRadioButton("Video")
        self.video_radio.setChecked(True)
        self.audio_radio = QRadioButton("Audio")
        media_type_layout.addWidget(self.video_radio)
        media_type_layout.addWidget(self.audio_radio)
        main_layout.addLayout(media_type_layout)

        self.quality_dropdown = QComboBox()
        main_layout.addWidget(self.quality_dropdown)

        self.save_as_input = QLineEdit()
        main_layout.addWidget(self.save_as_input)

        destination_layout = QHBoxLayout()
        self.destination_path_label = QLabel("Destination: [Not Selected]")
        self.browse_button = QPushButton("Browse...")
        destination_layout.addWidget(self.destination_path_label)
        destination_layout.addWidget(self.browse_button)
        main_layout.addLayout(destination_layout)

        self.playlist_checkbox = QCheckBox("Download entire playlist")
        self.playlist_checkbox.setVisible(False)
        main_layout.addWidget(self.playlist_checkbox)

        self.download_button = QPushButton("Download")
        main_layout.addWidget(self.download_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setVisible(False)
        main_layout.addWidget(self.cancel_button)
        
        self.show_in_folder_button = QPushButton("Show in Folder")
        self.show_in_folder_button.setVisible(False)
        main_layout.addWidget(self.show_in_folder_button)

        main_layout.addStretch()

        self.quality_dropdown.setEnabled(False)
        self.save_as_input.setEnabled(False)
        self.download_button.setEnabled(False)
        # --- End of UI Setup ---

        # 3. Create and start the worker thread.
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VidAudDownload()
    window.show()
    sys.exit(app.exec())