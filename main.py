import sys
from PySide6.QtWidgets import QApplication, QMainWindow

# 1. & 2. Define a class `VidAudDownload` that inherits from `QMainWindow`.
class VidAudDownload(QMainWindow):
    def __init__(self):
        super().__init__()

        # 3. Give the window the title and a default size.
        self.setWindowTitle("VidAudDownload")
        self.resize(800, 600)

# 4. Standard boilerplate to run the application.
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VidAudDownload()
    window.show()
    sys.exit(app.exec())