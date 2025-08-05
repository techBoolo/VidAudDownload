import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QLineEdit, QRadioButton, QComboBox, QPushButton,
    QCheckBox, QProgressBar, QLabel
)
from PySide6.QtCore import Qt

class VidAudDownload(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VidAudDownload")
        self.resize(800, 600)

        # 1. Create a central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # URL input field
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste video or playlist URL here")
        main_layout.addWidget(self.url_input)

        # Video/Audio radio buttons
        media_type_layout = QHBoxLayout()
        self.video_radio = QRadioButton("Video")
        self.video_radio.setChecked(True) # Default to Video
        self.audio_radio = QRadioButton("Audio")
        media_type_layout.addWidget(self.video_radio)
        media_type_layout.addWidget(self.audio_radio)
        main_layout.addLayout(media_type_layout)

        # Quality selection dropdown
        self.quality_dropdown = QComboBox()
        main_layout.addWidget(self.quality_dropdown)

        # "Save As" filename field
        self.save_as_input = QLineEdit()
        main_layout.addWidget(self.save_as_input)

        # Destination folder layout
        destination_layout = QHBoxLayout()
        self.destination_path_label = QLabel("Destination: [Not Selected]")
        self.browse_button = QPushButton("Browse...")
        destination_layout.addWidget(self.destination_path_label)
        destination_layout.addWidget(self.browse_button)
        main_layout.addLayout(destination_layout)

        # Playlist checkbox
        self.playlist_checkbox = QCheckBox("Download entire playlist")
        self.playlist_checkbox.setVisible(False)
        main_layout.addWidget(self.playlist_checkbox)

        # Download button
        self.download_button = QPushButton("Download")
        main_layout.addWidget(self.download_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setVisible(False)
        main_layout.addWidget(self.cancel_button)
        
        # Show in Folder button
        self.show_in_folder_button = QPushButton("Show in Folder")
        self.show_in_folder_button.setVisible(False)
        main_layout.addWidget(self.show_in_folder_button)
        
        main_layout.addStretch() # Pushes widgets to the top

        # 2. Initially disable widgets
        self.quality_dropdown.setEnabled(False)
        self.save_as_input.setEnabled(False)
        self.download_button.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VidAudDownload()
    window.show()
    sys.exit(app.exec())