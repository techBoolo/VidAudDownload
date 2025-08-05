import sys
import os
import configparser
import yt_dlp
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QLineEdit, QRadioButton, QComboBox, QPushButton,
    QCheckBox, QProgressBar, QLabel, QFileDialog
)
from PySide6.QtCore import Qt, QObject, Signal, QThread, QMetaObject

class Worker(QObject):
    info_ready = Signal(dict)
    progress = Signal(int)
    playlist_progress = Signal(str) # New signal for playlist status
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self._is_cancelled = False

    def validate_url(self, url):
        # (Identical to previous step)
        try:
            ydl_opts = {'extract_flat': True, 'force_generic_extractor': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: info = ydl.extract_info(url, download=False); self.info_ready.emit(info)
        except Exception as e: self.error.emit(f"Validation failed: {str(e)}")

    def start_download(self, download_info):
        self._is_cancelled = False
        
        def progress_hook(d):
            if self._is_cancelled: raise Exception('Download Cancelled')
            if d['status'] == 'downloading':
                if '%' in d['_percent_str']:
                    percent = int(float(d['_percent_str'].strip().replace('%', '')))
                    self.progress.emit(percent)
            elif d['status'] == 'finished':
                # For single videos, this signals completion. For playlists, it's handled after the loop.
                if not download_info['is_playlist']:
                    self.finished.emit({'status': 'finished', 'filename': d.get('filename')})

        # --- 1. Main logic change: Handle single vs. playlist ---
        try:
            # If it's NOT a playlist, use the simple download logic
            if not download_info['is_playlist']:
                ydl_opts = {
                    'format': download_info['format_id'],
                    'outtmpl': download_info['save_path'],
                    'progress_hooks': [progress_hook],
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([download_info['url']])
            
            # If it IS a playlist, use the iterative logic
            else:
                # First, extract the info for the entire playlist to get the list of entries
                with yt_dlp.YoutubeDL({'extract_flat': 'in_playlist'}) as ydl:
                    playlist_info = ydl.extract_info(download_info['url'], download=False)
                
                total_videos = len(playlist_info['entries'])
                
                # Iterate through each video in the playlist
                for i, entry in enumerate(playlist_info['entries']):
                    if self._is_cancelled: raise Exception('Download Cancelled')
                    
                    video_url = entry.get('url')
                    if not video_url: continue # Skip if entry has no URL

                    # Emit progress for the UI
                    status_msg = f"Playlist: Downloading {i + 1} of {total_videos}: {entry.get('title', 'Unknown Title')}"
                    self.playlist_progress.emit(status_msg)

                    # Sanitize filename for this specific video
                    sanitized_title = "".join([c for c in entry.get('title', f'video_{i+1}') if c.isalpha() or c.isdigit() or c in (' ', '_', '-')]).rstrip()
                    video_save_path = os.path.join(os.path.dirname(download_info['save_path']), sanitized_title + ".%(ext)s")

                    ydl_opts = {
                        'format': download_info['format_id'], 'outtmpl': video_save_path,
                        'progress_hooks': [progress_hook], 'noplaylist': True # Ensure we only download one video
                    }

                    try:
                        # Attempt to download with the user's selected format
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([video_url])
                    except yt_dlp.utils.DownloadError as e:
                        # Quality fallback logic
                        print(f"Format {download_info['format_id']} not available for '{entry.get('title')}'. Falling back. Error: {e}")
                        self.playlist_progress.emit(f"Format not available for '{entry.get('title')}'. Finding best available...")
                        
                        fallback_opts = { 'outtmpl': video_save_path, 'progress_hooks': [progress_hook], 'noplaylist': True }
                        with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                            # This time, let yt-dlp choose the best format automatically
                            ydl.download([video_url])
                
                # After the loop finishes, emit the final finished signal for the playlist
                self.finished.emit({'status': 'playlist_finished'})

        except Exception as e:
            if str(e) == 'Download Cancelled': print("Download successfully cancelled by user.")
            else: self.error.emit(f"Download Failed: {str(e)}")

    def cancel_download(self): self._is_cancelled = True


class VidAudDownload(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... (Identical __init__ setup as previous step, just add the new connection) ...
        self.setWindowTitle("VidAudDownload"); self.resize(800, 600); self.final_file_path = None
        self.settings_file = 'config.ini'
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.url_input = QLineEdit(); self.url_input.setPlaceholderText("Paste video or playlist URL here")
        main_layout.addWidget(self.url_input)
        media_type_layout = QHBoxLayout(); self.video_radio = QRadioButton("Video"); self.video_radio.setChecked(True)
        self.audio_radio = QRadioButton("Audio"); media_type_layout.addWidget(self.video_radio); media_type_layout.addWidget(self.audio_radio)
        main_layout.addLayout(media_type_layout)
        self.quality_dropdown = QComboBox(); main_layout.addWidget(self.quality_dropdown)
        self.save_as_input = QLineEdit(); main_layout.addWidget(self.save_as_input)
        destination_layout = QHBoxLayout(); self.destination_path_label = QLabel()
        self.browse_button = QPushButton("Browse..."); destination_layout.addWidget(self.destination_path_label); destination_layout.addWidget(self.browse_button)
        main_layout.addLayout(destination_layout)
        self.playlist_checkbox = QCheckBox("Download entire playlist"); self.playlist_checkbox.setVisible(False); main_layout.addWidget(self.playlist_checkbox)
        self.download_button = QPushButton("Download"); main_layout.addWidget(self.download_button)
        self.progress_bar = QProgressBar(); self.progress_bar.setValue(0); self.progress_bar.setVisible(False); main_layout.addWidget(self.progress_bar)
        self.status_label = QLabel("Ready"); self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter); main_layout.addWidget(self.status_label)
        self.cancel_button = QPushButton("Cancel"); self.cancel_button.setVisible(False); main_layout.addWidget(self.cancel_button)
        self.show_in_folder_button = QPushButton("Show in Folder"); self.show_in_folder_button.setVisible(False); main_layout.addWidget(self.show_in_folder_button)
        main_layout.addStretch(); self.quality_dropdown.setEnabled(False); self.save_as_input.setEnabled(False); self.download_button.setEnabled(False)
        self.thread = QThread(); self.worker = Worker(); self.worker.moveToThread(self.thread); self.thread.start()
        self.url_input.textChanged.connect(self.on_url_changed)
        self.video_radio.toggled.connect(self.on_url_changed)
        self.download_button.clicked.connect(self.on_download_clicked)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.browse_button.clicked.connect(self.open_folder_dialog)
        self.worker.info_ready.connect(self.on_info_ready)
        self.worker.progress.connect(self.update_progress)
        self.worker.playlist_progress.connect(self.update_playlist_progress) # New connection
        self.worker.finished.connect(self.on_download_finished)
        self.worker.error.connect(self.on_error)
        self.load_settings()

    def on_download_clicked(self):
        """Pass the playlist checkbox state to the worker."""
        # This is the only change in this method
        is_playlist = self.playlist_checkbox.isVisible() and self.playlist_checkbox.isChecked()
        
        sanitized_filename = "".join([c for c in self.save_as_input.text() if c.isalpha() or c.isdigit() or c in (' ', '_', '-')]).rstrip()
        save_path = os.path.join(self.destination_folder, sanitized_filename + ".%(ext)s")
        
        download_info = {
            'url': self.url_input.text(), 'format_id': self.quality_dropdown.currentData(),
            'save_path': save_path, 'is_playlist': is_playlist
        }
        self.prepare_ui_for_download()
        QMetaObject.invokeMethod(self.worker, "start_download", Qt.ConnectionType.QueuedConnection, Q_ARG(dict, download_info))
    
    # 2. New slot to handle playlist progress updates
    def update_playlist_progress(self, status_string):
        """Updates the status label with playlist-specific progress."""
        self.status_label.setText(status_string)

    # --- Other methods are identical to Step 9 ---
    def load_settings(self):
        config = configparser.ConfigParser();
        if os.path.exists(self.settings_file): config.read(self.settings_file); self.destination_folder = config.get('Settings', 'destination_folder', fallback=os.path.expanduser("~"))
        else: self.destination_folder = os.path.expanduser("~/Downloads")
        self.destination_path_label.setText(f"Destination: {self.destination_folder}")
    def save_settings(self):
        config = configparser.ConfigParser(); config['Settings'] = {'destination_folder': self.destination_folder}
        with open(self.settings_file, 'w') as configfile: config.write(configfile)
    def open_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.destination_folder)
        if folder: self.destination_folder = folder; self.destination_path_label.setText(f"Destination: {self.destination_folder}"); self.save_settings()
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
        # Only show the "Show in Folder" button for single files, not playlists.
        if result_dict.get('status') == 'finished':
             self.show_in_folder_button.setVisible(True)
        self.reset_ui_after_download()
    def on_error(self, error_message):
        self.status_label.setText(error_message)
        self.reset_ui_after_download()
    def prepare_ui_for_download(self):
        self.url_input.setEnabled(False); self.quality_dropdown.setEnabled(False); self.download_button.setVisible(False)
        self.progress_bar.setVisible(True); self.progress_bar.setValue(0); self.cancel_button.setVisible(True)
        self.status_label.setText("Downloading...")
    def reset_ui_after_download(self):
        self.url_input.setEnabled(True); self.download_button.setVisible(True); self.download_button.setEnabled(True)
        self.quality_dropdown.setEnabled(True); self.progress_bar.setVisible(False); self.cancel_button.setVisible(False)
    def reset_ui_for_new_url(self):
        self.status_label.setText("Validating URL..."); self.quality_dropdown.clear(); self.quality_dropdown.setEnabled(False)
        self.save_as_input.clear(); self.save_as_input.setEnabled(False); self.download_button.setEnabled(False)
        self.playlist_checkbox.setVisible(False); self.show_in_folder_button.setVisible(False); self.progress_bar.setVisible(False)
        self.final_file_path = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VidAudDownload()
    window.show()
    sys.exit(app.exec())