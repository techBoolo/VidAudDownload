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

    def validate_url(self, url):
        try:
            # Use 'extract_flat' for playlists to get entries faster.
            # 'force_generic_extractor' can also help avoid fetching too much data initially.
            ydl_opts = {'extract_flat': True, 'force_generic_extractor': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                self.info_ready.emit(info)
        except yt_dlp.utils.DownloadError:
            self.error.emit("Invalid or Unsupported URL")
        except Exception as e:
            self.error.emit(f"An error occurred: {str(e)}")


class VidAudDownload(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VidAudDownload")
        self.resize(800, 600)

        # --- UI Setup (Identical to previous step) ---
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

        # Connect signals to slots
        self.url_input.textChanged.connect(self.on_url_changed)
        # Re-fetch info if the user changes the media type
        self.video_radio.toggled.connect(self.on_url_changed)
        self.worker.info_ready.connect(self.on_info_ready)
        self.worker.error.connect(self.on_error)

    def on_url_changed(self, url=""): # Default arg to handle radio button signal
        if not self.url_input.text():
            return
            
        self.status_label.setText("Validating URL...")
        self.quality_dropdown.setEnabled(False)
        self.save_as_input.setEnabled(False)
        self.download_button.setEnabled(False)
        self.playlist_checkbox.setVisible(False)
        
        QMetaObject.invokeMethod(self.worker, "validate_url", Qt.ConnectionType.QueuedConnection, Q_ARG(str, self.url_input.text()))

    def on_info_ready(self, info):
        """
        Slot to handle the `info_ready` signal. Populates the UI with fetched data.
        """
        # 1. Clear previous items
        self.quality_dropdown.clear()
        
        # In case of playlist, info might be for the whole list. We need info for the first video.
        first_video_info = info['entries'][0] if 'entries' in info else info

        # 2. Check for playlist and show checkbox
        if 'entries' in info:
            self.playlist_checkbox.setVisible(True)
            self.save_as_input.setText(info.get('title', 'Playlist'))
        else:
            self.playlist_checkbox.setVisible(False)
            self.save_as_input.setText(first_video_info.get('title', ''))

        # 3. Parse formats and populate quality dropdown
        formats = first_video_info.get('formats', [])
        for f in reversed(formats): # Start with best quality
            # User wants Video
            if self.video_radio.isChecked():
                # We need formats that have both video and audio
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    resolution = f.get('resolution', 'N/A')
                    fps = f.get('fps')
                    filesize = f.get('filesize_approx')
                    filesize_str = f"~{filesize / (1024*1024):.2f} MB" if filesize else "Size N/A"
                    display_text = f"Video: {resolution} ({fps}fps) - {filesize_str}"
                    # Store the format_id with the item
                    self.quality_dropdown.addItem(display_text, f['format_id'])
            # User wants Audio only
            else:
                # We need formats that have audio but no video
                if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                    abr = f.get('abr') # Average bitrate
                    filesize = f.get('filesize_approx')
                    filesize_str = f"~{filesize / (1024*1024):.2f} MB" if filesize else "Size N/A"
                    display_text = f"Audio: {abr}kbps ({f['ext']}) - {filesize_str}"
                    self.quality_dropdown.addItem(display_text, f['format_id'])
        
        # 4. Enable UI controls
        if self.quality_dropdown.count() > 0:
            self.quality_dropdown.setCurrentIndex(0) # Select best quality by default
            self.quality_dropdown.setEnabled(True)
            self.download_button.setEnabled(True)
            self.status_label.setText("Ready to download")
        else:
            self.status_label.setText("No compatible formats found.")

        self.save_as_input.setEnabled(True)


    def on_error(self, error_message):
        self.status_label.setText(error_message)
        self.quality_dropdown.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VidAudDownload()
    window.show()
    sys.exit(app.exec())