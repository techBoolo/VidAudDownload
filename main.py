import sys
import yt_dlp
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QLineEdit, QRadioButton, QComboBox, QPushButton,
    QCheckBox, QProgressBar, QLabel
)
from PySide6.QtCore import Qt, QObject, Signal, QThread, QMetaObject

class Worker(QObject):
    info_ready = Signal(dict)
    progress = Signal(int)
    finished = Signal(dict)
    error = Signal(str)

    # 1. Create the validate_url method.
    def validate_url(self, url):
        """
        Uses yt-dlp to validate the URL and extract info.
        """
        try:
            # Use a yt-dlp context manager to extract info without downloading.
            with yt_dlp.YoutubeDL({'noplaylist': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                # If successful, emit the info dictionary.
                self.info_ready.emit(info)
        except yt_dlp.utils.DownloadError:
            # If it fails, emit an error message.
            self.error.emit("Invalid or Unsupported URL")
        except Exception as e:
            # Catch other potential errors.
            self.error.emit(f"An error occurred: {str(e)}")


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

        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.start()

        # 2. Connect signals to slots.
        self.url_input.textChanged.connect(self.on_url_changed)
        self.worker.info_ready.connect(self.on_info_ready)
        self.worker.error.connect(self.on_error)

    def on_url_changed(self, url):
        """
        When the URL text changes, trigger the validation on the worker thread.
        """
        # Reset UI elements for a new URL
        self.status_label.setText("Validating URL...")
        self.quality_dropdown.setEnabled(False)
        self.save_as_input.setEnabled(False)
        self.download_button.setEnabled(False)
        self.playlist_checkbox.setVisible(False)
        
        # Asynchronously invoke the validate_url method on the worker's thread.
        QMetaObject.invokeMethod(self.worker, "validate_url", Qt.ConnectionType.QueuedConnection, Q_ARG(str, url))

    def on_info_ready(self, info):
        """
        Slot to handle the `info_ready` signal from the worker.
        """
        # This will be fully implemented in Step 5.
        # For now, we'll just confirm it works.
        self.status_label.setText(f"Successfully found: {info['title']}")
        print("Info received:", info)

    def on_error(self, error_message):
        """
        Slot to handle the `error` signal from the worker.
        """
        self.status_label.setText(error_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VidAudDownload()
    window.show()
    sys.exit(app.exec())