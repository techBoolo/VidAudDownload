import sys
import os
import configparser # New import
import yt_dlp
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QLineEdit, QRadioButton, QComboBox, QPushButton,
    QCheckBox, QProgressBar, QLabel, QFileDialog # New import
)
from PySide6.QtCore import Qt, QObject, Signal, QThread, QMetaObject

class Worker(QObject):
    # (Worker class is identical to previous step)
    info_ready = Signal(dict)
    progress = Signal(int)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self._is_cancelled = False

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

    def start_download(self, download_info):
        self._is_cancelled = False
        def progress_hook(d):
            if self._is_cancelled: raise Exception('Download Cancelled')
            if d['status'] == 'downloading':
                if '%' in d['_percent_str']:
                    percent = int(float(d['_percent_str'].strip().replace('%', '')))
                    self.progress.emit(percent)
            elif d['status'] == 'finished':
                if self._is_cancelled: raise Exception('Download Cancelled')
                self.finished.emit({'status': 'finished', 'filename': d.get('filename')})
        ydl_opts = {
            'format': download_info['format_id'], 'outtmpl': download_info['save_path'],
            'progress_hooks': [progress_hook],
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([download_info['url']])
        except Exception as e:
            if str(e) == 'Download Cancelled': print("Download successfully cancelled by user.")
            else: self.error.emit(f"Download Failed: {str(e)}")
    
    def cancel_download(self):
        self._is_cancelled = True


class VidAudDownload(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VidAudDownload")
        self.resize(800, 600)
        self.final_file_path = None
        # 2. Define path for settings file
        self.settings_file = 'config.ini'

        # --- UI Setup ---
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
        # The label will be set by load_settings()
        self.destination_path_label = QLabel()
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

        # Connections
        self.url_input.textChanged.connect(self.on_url_changed)
        self.video_radio.toggled.connect(self.on_url_changed)
        self.download_button.clicked.connect(self.on_download_clicked)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        # 3. Connect the "Browse..." button
        self.browse_button.clicked.connect(self.open_folder_dialog)
        self.worker.info_ready.connect(self.on_info_ready)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.error.connect(self.on_error)
        
        # 2. Call load_settings on startup.
        self.load_settings()

    # 2. New methods for settings persistence
    def load_settings(self):
        """Loads destination folder from config.ini, defaulting to Downloads."""
        config = configparser.ConfigParser()
        if os.path.exists(self.settings_file):
            config.read(self.settings_file)
            # Use fallback for safety
            self.destination_folder = config.get('Settings', 'destination_folder', fallback=os.path.expanduser("~"))
        else:
            self.destination_folder = os.path.expanduser("~/Downloads")
        
        self.destination_path_label.setText(f"Destination: {self.destination_folder}")

    def save_settings(self):
        """Saves the current destination folder to config.ini."""
        config = configparser.ConfigParser()
        config['Settings'] = {'destination_folder': self.destination_folder}
        with open(self.settings_file, 'w') as configfile:
            config.write(configfile)

    # 4. New slot for the "Browse..." button
    def open_folder_dialog(self):
        """Opens a dialog for the user to select a folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.destination_folder)
        if folder: # If the user selected a folder and didn't cancel
            self.destination_folder = folder
            self.destination_path_label.setText(f"Destination: {self.destination_folder}")
            self.save_settings()

    def on_download_clicked(self):
        # This method is now updated to use the saved destination_folder
        sanitized_filename = "".join([c for c in self.save_as_input.text() if c.isalpha() or c.isdigit() or c in (' ', '_', '-')]).rstrip()
        save_path = os.path.join(self.destination_folder, sanitized_filename + ".%(ext)s")
        download_info = {'url': self.url_input.text(), 'format_id': self.quality_dropdown.currentData(), 'save_path': save_path}
        self.prepare_ui_for_download()
        QMetaObject.invokeMethod(self.worker, "start_download", Qt.ConnectionType.QueuedConnection, Q_ARG(dict, download_info))

    # --- Other methods are identical to Step 8 ---
    def on_url_changed(self, url=""):
        if not self.url_input.text(): return
        self.reset_ui_for_new_url()
        QMetaObject.invokeMethod(self.worker, "validate_url", Qt.ConnectionType.QueuedConnection, Q_ARG(str, self.url_input.text()))
    def on_info_ready(self, info):
        self.quality_dropdown.clear()
        first_video_info = info['entries'][0] if 'entries' in info else info
        if 'entries' in info: self.playlist_checkbox.setVisible(True)
        else: self.playlist_checkbox.setVisible(False)
        self.save_as_input.setText(first_video_info.get('title', ''))
        formats = first_video_info.get('formats', [])
        for f in reversed(formats):
            if self.video_radio.isChecked():
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    display_text = f"Video: {f.get('resolution', 'N/A')} ({f.get('fps')}fps)"
                    self.quality_dropdown.addItem(display_text, f['format_id'])
            else:
                if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                    display_text = f"Audio: {f.get('abr')}kbps ({f['ext']})"
                    self.quality_dropdown.addItem(display_text, f['format_id'])
        if self.quality_dropdown.count() > 0:
            self.quality_dropdown.setCurrentIndex(0)
            self.quality_dropdown.setEnabled(True)
            self.download_button.setEnabled(True)
            self.status_label.setText("Ready to download")
        else: self.status_label.setText("No compatible formats found.")
        self.save_as_input.setEnabled(True)
    def update_progress(self, percent):
        self.progress_bar.setValue(percent)
    def on_cancel_clicked(self):
        self.status_label.setText("Cancelling...")
        self.worker.cancel_download()
        self.reset_ui_after_download()
        self.status_label.setText("Download Cancelled")
    def on_download_finished(self, result_dict):
        self.progress_bar.setValue(100)
        self.status_label.setText("Download Complete")
        self.final_file_path = result_dict.get('filename')
        self.show_in_folder_button.setVisible(True)
        self.reset_ui_after_download()
    def on_error(self, error_message):
        self.status_label.setText(error_message)
        self.reset_ui_after_download()
    def prepare_ui_for_download(self):
        self.url_input.setEnabled(False)
        self.quality_dropdown.setEnabled(False)
        self.download_button.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.cancel_button.setVisible(True)
        self.status_label.setText("Downloading...")
    def reset_ui_after_download(self):
        self.url_input.setEnabled(True)
        self.download_button.setVisible(True)
        self.download_button.setEnabled(True)
        self.quality_dropdown.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
    def reset_ui_for_new_url(self):
        self.status_label.setText("Validating URL...")
        self.quality_dropdown.clear()
        self.quality_dropdown.setEnabled(False)
        self.save_as_input.clear()
        self.save_as_input.setEnabled(False)
        self.download_button.setEnabled(False)
        self.playlist_checkbox.setVisible(False)
        self.show_in_folder_button.setVisible(False)
        self.progress_bar.setVisible(False)
        self.final_file_path = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VidAudDownload()
    window.show()
    sys.exit(app.exec())