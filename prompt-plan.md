Of course. Here is a detailed, multi-stage blueprint for building the
`VidAudDownload` application.

This plan is structured into small, iterative chunks. Each chunk is then broken
down into a specific prompt designed for a code-generation LLM. The prompts
build on each other sequentially, ensuring that each step is an incremental
addition to a working base, following software development best practices.

---

### **Development Blueprint: VidAudDownload**

The project will be built iteratively. Each step represents a distinct,
testable feature set.

*   **Phase 1: Foundation (Steps 1-3)**
    *   **Goal:** Establish the core application structure.
    *   **Steps:** Create the main window, lay out the static UI, and set up
        the critical non-blocking thread architecture. At the end of this
phase, we will have a non-functional but structurally sound application.

*   **Phase 2: Core Logic (Steps 4-7)**
    *   **Goal:** Implement the primary download functionality for a single
        video.
    *   **Steps:** Wire up URL validation, fetch video/audio information,
        populate the UI with that data, implement the download function with
progress feedback, and handle the final success/error states. At the end of
this phase, the core feature will be fully functional.

*   **Phase 3: Feature Enhancement (Steps 8-10)**
    *   **Goal:** Add user control, configuration, and advanced features.
    *   **Steps:** Implement the cancel functionality, add the destination
        folder selection with persistence, and then add the logic for handling
playlists. At the end of this phase, the application will be feature-complete
according to the spec.

*   **Phase 4: Final Polish (Step 11)**
    *   **Goal:** Refine the user experience and ensure all parts are
        seamlessly integrated.
    *   **Step:** Add quality-of-life improvements like clipboard auto-pasting
        and conduct a final wiring check.

---

### **LLM Implementation Prompts**

Below are the series of prompts to be provided to a code-generation LLM.

---
### **Step 1: Project Skeleton and Main Window**

**Context:** The first step is to create the absolute basic foundation of the
application. This involves setting up the main Python file and creating an
empty window that will serve as our canvas. This ensures we have a working
entry point before adding any complexity.

```text
Create a Python application named "VidAudDownload" using the PySide6 library.

1.  Create a file named `main.py`.
2.  In this file, define a class `VidAudDownload` that inherits from
    `QMainWindow`.
3.  Give the window the title "VidAudDownload" and set a default size of
    800x600 pixels.
4.  Include the standard boilerplate code to initialize the `QApplication`,
    create an instance of our `VidAudDownload` window, show it, and start the
application's event loop.
```
---
### **Step 2: Building the Static UI Layout**

**Context:** With the main window established, we will now populate it with all
the necessary UI elements as defined in the specification. At this stage, none
of these elements will have any logic attached. The goal is to build the
complete visual layout so we can wire them up in subsequent steps.

```text
Using the `VidAudDownload` class from the previous step, let's build the static
user interface. Do not add any functionality yet, only create and arrange the
widgets.

1.  Create a central widget and use layouts (e.g., `QVBoxLayout` and
    `QHBoxLayout`) to arrange the following widgets vertically:
    *   An input field (`QLineEdit`) for the URL. Set its placeholder text to
        "Paste video or playlist URL here".
    *   A layout containing two radio buttons (`QRadioButton`): "Video" and
        "Audio".
    *   A dropdown menu (`QComboBox`) for quality selection.
    *   An editable text field (`QLineEdit`) for the "Save As" filename.
    *   A layout containing a non-editable label to display the destination
        path and a "Browse..." button (`QPushButton`).
    *   A "Download entire playlist" checkbox (`QCheckBox`), which should be
        hidden by default.
    *   A "Download" button (`QPushButton`).
    *   A progress bar (`QProgressBar`), initially at 0% and hidden.
    *   A status label (`QLabel`) for messages (e.g., "Ready",
        "Downloading...", "Complete").
    *   A "Cancel" button (`QPushButton`), hidden by default.
    *   A "Show in Folder" button (`QPushButton`), hidden by default.

2.  Initially, disable the quality dropdown, "Save As" field, and "Download"
    button.
```
---
### **Step 3: Creating the Threading Foundation**

**Context:** This is a critical architectural step. To prevent the UI from
freezing during network operations, we will create a dedicated worker class
that runs on a separate thread. This step defines the communication channels
(signals) between the worker and the UI. We will not add the `yt-dlp` logic
yet, just the threading structure.

```text
Modify the `main.py` file to establish the essential threading architecture.

1.  Create a new class named `Worker` that inherits from `QObject`. This class
    will handle all long-running tasks.
2.  Define the following custom signals in the `Worker` class. These will be
    used to communicate back to the main UI thread:
    *   `info_ready(info_dict)`: To send the extracted video information (as a
        dictionary).
    *   `progress(percent)`: To send download progress (as an integer).
    *   `finished(success_dict)`: To signal successful completion.
    *   `error(error_message)`: To signal that an error occurred (as a string).

3.  In the `VidAudDownload` class constructor (`__init__`), create an instance
    of this `Worker` class and a `QThread`. Move the worker to the new thread
and start the thread. This ensures the worker is ready to receive tasks.
```
---
### **Step 4: Implementing URL Validation**

**Context:** Now we will connect the UI to the backend for the first time. When
the user enters a URL, the validation task will be offloaded to the worker
thread. The worker will then send a signal back to the UI indicating success or
failure. This implements the core asynchronous workflow.

```text
Let's bring the application to life by implementing URL validation.

1.  In the `Worker` class, create a new method called `validate_url(url)`. This
    method will:
    *   Use the `yt_dlp` library to extract information for the given `url`.
        Use a `try...except` block to catch any errors (like `DownloadError`).
    *   If successful, emit the `info_ready` signal with the extracted
        information dictionary.
    *   If it fails, emit the `error` signal with a message like "Invalid or
        Unsupported URL".

2.  In the `VidAudDownload` class:
    *   Connect the `textChanged` signal of the URL input field to a new slot
        method.
    *   This new slot will trigger the `worker.validate_url(url)` method.
    *   Create slots to handle the worker's `info_ready` and `error` signals.
    *   The `on_error` slot should display the received error message in the
        status label and reset/disable the relevant UI elements.
```
---
### **Step 5: Populating the UI with Video Data**

**Context:** Building on the previous step, once the `info_ready` signal is
received, the UI needs to display the data to the user. This step involves
populating the dropdowns and filename, and enabling the controls for the user
to proceed.

```text
Now, let's implement the `on_info_ready` slot in the `VidAudDownload` class to
process the data received from the worker.

1.  The `on_info_ready(info)` slot will:
    *   Clear any previous items from the quality dropdown.
    *   Check if the received `info` is for a playlist (`'entries' in info`).
        If so, make the "Download entire playlist" checkbox visible.
    *   Populate the "Save As" field with the video's title (`info['title']`).
    *   Parse the `info['formats']` list. Populate the quality dropdown with
        user-friendly strings for available video resolutions and audio
bitrates. Store the format ID with each entry.
    *   Select the best available format by default in the dropdown.
    *   Enable the quality dropdown, "Save As" field, and the "Download"
        button.
    *   Update the status label to "Ready to download".
```
---
### **Step 6: Implementing the Download Action and Progress Bar**

**Context:** This is the core download functionality. The "Download" button
will trigger a method on the worker. The worker will use `yt-dlp`'s progress
hooks to continuously emit the `progress` signal, which the UI will use to
update the progress bar.

```text
Let's implement the main download logic.

1.  In the `Worker` class, create a new method `start_download(download_info)`.
    This method will accept a dictionary containing the `url`, selected
`format_id`, `save_path`, and whether it's a `playlist`.
    *   Define a progress hook function that `yt-dlp` can call. This hook will
        calculate the percentage and `emit(self.progress)`.
    *   Set up the `yt_dlp` options dictionary, including the save path
        (`outtmpl`) and the progress hook.
    *   Call `yt_dlp.YoutubeDL(ydl_opts).download([url])`.
    *   Wrap this call in a `try...except` block to catch errors.

2.  In the `VidAudDownload` class:
    *   Connect the "Download" button's `clicked` signal to a new
        `on_download_clicked` slot.
    *   This slot will gather all the necessary info (URL, selected format ID,
        save path, playlist checkbox state), package it into a dictionary, and
call `worker.start_download()`.
    *   It will also prepare the UI for downloading: hide the "Download"
        button, show the progress bar and "Cancel" button, and update the
status label.
    *   Create a slot `update_progress(percent)` and connect it to the worker's
        `progress` signal. This slot will set the value of the progress bar.
```
---
### **Step 7: Handling Download Completion and Failures**

**Context:** A download doesn't run forever. We need to handle the end states.
This involves using the `finished` and `error` signals from the worker to
inform the user of the outcome and reset the UI to an appropriate state.

```text
Let's handle the final states of the download process.

1.  In the `Worker.start_download` method:
    *   After a successful download, emit the `finished` signal with a
        dictionary containing the final save path and filename.
    *   If any exception occurs during the download, emit the `error` signal
        with a user-friendly message like "Download Failed: [Reason]".

2.  In the `VidAudDownload` class:
    *   Create a slot `on_download_finished(result_dict)` and connect it to the
        worker's `finished` signal. This slot will:
        *   Set the progress bar to 100%.
        *   Update the status label to "Download Complete".
        *   Make the "Show in Folder" button visible.
        *   Store the final file path so "Show in Folder" knows what to open.
        *   Reset other UI elements for the next download.
    *   The existing `on_error` slot will handle download failures, displaying
        the error message and resetting the UI.
```
---
### **Step 8: Implementing the Cancel Button**

**Context:** Users need control. The cancel button will set a flag in the
worker thread. The download process within the worker must check this flag to
know when to abort gracefully.

```text
Let's implement the download cancellation feature.

1.  In the `Worker` class, add an instance attribute `_is_cancelled = False`.
2.  Create a public method `cancel_download()`. When called, it will set
    `_is_cancelled` to `True`.
3.  Modify the `yt-dlp` progress hook in `start_download`. In addition to
    emitting progress, it must check `if self._is_cancelled:`. If true, it
should `raise Exception('Download Cancelled')`. This will abort the download
process.
4.  In the `start_download` method, before starting, reset `_is_cancelled` to
    `False`. The `except` block should check for the 'Download Cancelled'
message and handle it cleanly without emitting an error.

5.  In the `VidAudDownload` class, connect the "Cancel" button's `clicked`
    signal to the `worker.cancel_download()` method.
```
---
### **Step 9: Adding Destination Folder Logic and Persistence**

**Context:** This step adds file dialogs and makes the application remember the
user's chosen download folder between sessions, improving usability.

```text
Let's implement the destination folder selection and make it persistent.

1.  Use Python's built-in `configparser` library.
2.  In the `VidAudDownload` class constructor:
    *   Define a path for a settings file (e.g., `config.ini`).
    *   Implement a `load_settings()` method. It should read the last saved
        folder path from the config file. If the file or setting doesn't exist,
it should default to the system's standard "Downloads" folder. Call this method
on startup.
    *   Update the destination path label with this value.
    *   Implement a `save_settings()` method that writes the current
        destination path to the config file.

3.  Connect the "Browse..." button's `clicked` signal to a new
    `open_folder_dialog` slot.
4.  The `open_folder_dialog` slot will use `QFileDialog.getExistingDirectory`
    to let the user pick a folder. If a folder is chosen, update the
destination path label and call `save_settings()`.
```
---
### **Step 10: Implementing Playlist Logic**

**Context:** Now we will enhance the download logic to handle playlists. This
involves iterating through the playlist entries and calling the download
function for each one, while providing clear feedback to the user.

```text
Modify the download logic to handle playlists correctly.

1.  In the `Worker.start_download` method:
    *   Check the `download_info` dictionary for the `is_playlist` flag.
    *   If `False`, the logic remains as is.
    *   If `True`, instead of just downloading, the method should:
        *   First, use `yt-dlp` to extract the info for the entire playlist.
        *   Then, iterate through the `info['entries']` list.
        *   Inside the loop, for each video entry, call the download logic.
        *   **Crucially**, update a status signal (you may need a new one, or
            overload the `progress` signal) to let the UI know which file is
being downloaded (e.g., "Downloading 5 of 20: Video Title").
        *   Implement the quality fallback logic as specified: try the selected
            format, and if it fails, get the info for that specific video and
choose the next best format automatically.
2.  In the `VidAudDownload` class, update the status label handling to
    correctly display the detailed playlist progress messages from the worker.
```
---
### **Step 11: Final Polish and Wiring**

**Context:** The final step is to add small quality-of-life improvements and
ensure all components work together perfectly. This includes the clipboard
auto-paste feature and a final review of the application's state management.

```text
Let's add the final polishing touches to complete the application.

1.  **Implement Clipboard Auto-Paste:**
    *   In the `VidAudDownload` class, override the `event(self, event)`
        method.
    *   Check if the event is a `QEvent.WindowActivate` (meaning the window
        gained focus).
    *   If it is, get the system clipboard's text.
    *   Use a simple regex to check if the text looks like a URL.
    *   If it is a URL and it's different from the text already in the URL
        input field, set the input field's text to the clipboard content.

2.  **Review UI State Management:**
    *   Go through the entire workflow and ensure all buttons and fields are
        enabled/disabled correctly at every stage (e.g., after completion,
after cancellation, after an error).
    *   Make sure the UI resets cleanly and is ready for a new download after
        any operation concludes.
    *   Confirm the playlist checkbox visibility is handled correctly on both
        playlist and single video URLs.
```
