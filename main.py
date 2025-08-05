import sys
import os
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
            ydl_opts = {'extract_flat': True, 'force_generic_extractor': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                self.info_ready.emit(info)
        except yt_dlp.utils.DownloadError:
            self.error.emit("Invalid or Unsupported URL")
        except Exception as e:
            self.error.emit(f"An error occurred: {str(e)}")

    # 1. Create the start_download method.
    def start_download(self, download_info):
        """
        Starts the download process using yt-dlp.
        """
        def progress_hook(d):
            if d['status'] == 'downloading':
                # Extract percentage and emit it.
                # The percent string can sometimes be ' N/A', so handle that.
                if '%' in d['_percent_str']:
                    percent = int(float(d['_percent_str'].strip().replace('%', '')))
                    self.progress.emit(percent)

        # Set up the options for yt-dlp
        ydl_opts = {
            'format': download_info['format_id'],
            'outtmpl': download_info['save_path'],
            'progress_hooks': [progress_hook],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([download_info['url']])
        except Exception as e:
            self.error.emit(f"Download failed: {str(e)}")


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
        # For now, we'll hardcode the destination. This will be updated in a later step.
        self.destination_folder = os.path.expanduser("~/Downloads")
        self.destination_path_label = QLabel(f"Destination: {self.destination_folder}")
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

        # 2. Connect new signals and slots
        self.url_input.textChanged.connect(self.on_url_changed)
        self.video_radio.toggled.connect(self.on_url_changed)
        self.download_button.clicked.connect(self.on_download_clicked) # New connection
        self.worker.info_ready.connect(self.on_info_ready)
        self.worker.progress.connect(self.update_progress) # New connection
        self.worker.error.connect(self.on_error)

    def on_url_changed(self, url=""):
        if not self.url_input.text():
            return
        self.status_label.setText("Validating URL...")
        self.quality_dropdown.setEnabled(False)
        self.save_as_input.setEnabled(False)
        self.download_button.setEnabled(False)
        self.playlist_checkbox.setVisible(False)
        QMetaObject.invokeMethod(self.worker, "validate_url", Qt.ConnectionType.QueuedConnection, Q_ARG(str, self.url_input.text()))

    def on_info_ready(self, info):
        # (Identical to previous step)
        self.quality_dropdown.clear()
        first_video_info = info['entries'][0] if 'entries' in info else info
        if 'entries' in info:
            self.playlist_checkbox.setVisible(True)
            self.save_as_input.setText(info.get('title', 'Playlist'))
        else:
            self.playlist_checkbox.setVisible(False)
            self.save_as_input.setText(first_video_info.get('title', ''))
        formats = first_video_info.get('formats', [])
        for f in reversed(formats):
            if self.video_radio.isChecked():
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    resolution = f.get('resolution', 'N/A')
                    fps = f.get('fps')
                    filesize = f.get('filesize_approx')
                    filesize_str = f"~{filesize / (1024*1024):.2f} MB" if filesize else "Size N/A"
                    display_text = f"Video: {resolution} ({fps}fps) - {filesize_str}"
                    self.quality_dropdown.addItem(display_text, f['format_id'])
            else:
                if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                    abr = f.get('abr')
                    filesize = f.get('filesize_approx')
                    filesize_str = f"~{filesize / (1024*1024):.2f} MB" if filesize else "Size N/A"
                    display_text = f"Audio: {abr}kbps ({f['ext']}) - {filesize_str}"
                    self.quality_dropdown.addItem(display_text, f['format_id'])
        if self.quality_dropdown.count() > 0:
            self.quality_dropdown.setCurrentIndex(0)
            self.quality_dropdown.setEnabled(True)
            self.download_button.setEnabled(True)
            self.status_label.setText("Ready to download")
        else:
            self.status_label.setText("No compatible formats found.")
        self.save_as_input.setEnabled(True)

    def on_download_clicked(self):
        """
        Gathers info and triggers the download on the worker thread.
        """
        # Construct the save path. yt-dlp will add the correct extension.
        # We sanitize the filename to avoid issues with special characters.
        sanitized_filename = "".join([c for c in self.save_as_input.text() if c.isalpha() or c.isdigit() or c in (' ', '_', '-')]).rstrip()
        save_path = os.path.join(self.destination_folder, sanitized_filename)

        # Package all the info the worker needs.
        download_info = {
            'url': self.url_input.text(),
            'format_id': self.quality_dropdown.currentData(),
            'save_path': save_path,
        }
        
        # Prepare UI for download
        self.download_button.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.cancel_button.setVisible(True)
        self.status_label.setText("Downloading...")
        self.url_input.setEnabled(False)
        self.quality_dropdown.setEnabled(False)
        
        # Asynchronously call the worker's start_download method.
        QMetaObject.invokeMethod(self.worker, "start_download", Qt.ConnectionType.QueuedConnection, Q_ARG(dict, download_info))

    def update_progress(self, percent):
        """
        Sets the value of the progress bar.
        """
        self.progress_bar.setValue(percent)

    def on_error(self, error_message):
        self.status_label.setText(error_message)
        # We will add full UI reset logic in the next step.

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VidAudDownload()
    window.show()
    sys.exit(app.exec())