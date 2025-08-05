# VidAudDownload

A simple yet powerful desktop application for downloading videos and audio from various websites, built with Python and PySide6. The app features a clean, non-freezing user interface by handling all network operations on a separate thread.

![VidAudDownload Screenshot](https://i.imgur.com/your-screenshot-url.png) 
*(Note: You should replace the above URL with a real screenshot of your application)*

---

### 🚨 **Important: Use the `dev` Branch** 🚨

This project uses a Git workflow where the most up-to-date code with the latest features and bug fixes resides on the **`dev`** branch. The `main` branch may be a stable but older version.

To ensure you are using the correct and most complete version of this application, please make sure you are on the `dev` branch after cloning the repository.

```bash
# After cloning, switch to the dev branch
git checkout dev
```

---

### Features

-   **Video & Audio Downloads:** Choose to download the full video or extract audio only.
-   **Quality Selection:** A dropdown menu is populated with available formats and resolutions.
-   **Playlist Support:** Download an entire playlist with a single click.
-   **Asynchronous UI:** The user interface remains responsive and never freezes during validation or downloading.
-   **Robust Error Handling:** Features a quality fallback system; if a chosen format fails, the app automatically tries to download the next best quality.
-   **Download Cancellation:** Cancel any download that is in progress.
-   **Persistent Destination:** Choose a download folder, and the application will remember it for next time.
-   **Clipboard Auto-Paste:** Automatically pastes a valid URL from your clipboard when the app window gains focus.
-   **Cross-Platform:** Built to run on Windows, macOS, and Linux.

---

### Prerequisites

Before you begin, ensure you have the following installed on your system:

1.  **Python 3.8+**
2.  **pip** (usually included with Python)
3.  **Git**
4.  **ffmpeg:** This is a **critical dependency** for merging video and audio streams. `yt-dlp` will not be able to download the best quality formats without it.
    -   Follow the official installation guide here: [yt-dlp Dependencies](https://github.com/yt-dlp/yt-dlp#dependencies)

---

### Installation & Setup

Follow these steps to get the application running on your local machine.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/VidAudDownload.git
    ```

2.  **Navigate into the project directory:**
    ```bash
    cd VidAudDownload
    ```

3.  **Switch to the `dev` branch (Most Important Step):**
    ```bash
    git checkout dev
    ```

4.  **Install the required Python libraries:**
    Create a `requirements.txt` file (as shown in the next section) and run:
    ```bash
    pip install -r requirements.txt
    ```
    Alternatively, you can install them manually:
    ```bash
    pip install PySide6 yt-dlp
    ```

---

### Running the Application

Once the setup is complete, you can run the application with the following command:

```bash
python main.py
```
*(On some systems, you may need to use `python3`)*

---
### `requirements.txt` File

For easy installation, create a file named `requirements.txt` in the same directory as your `main.py` file with the following content:

```
pyside6
yt-dlp
```
```

This README file clearly sets expectations, emphasizes the required branch, and provides all the necessary steps for another developer (or your future self) to get the project running smoothly.