# PRD: PySide6 Log Watcher Application

| Version | Date       | Author          | Change Description |
| :------ | :--------- | :-------------- | :----------------- |
| 1.0     | 2025-11-08 | Specifier (AI)  | Initial draft (Fyne) |
| 2.0     | 2025-11-08 | Specifier (AI)  | Tech Stack Migration to Python/PySide6 |
| 3.0     | 2025-11-08 | Specifier (AI)  | **Major UI Refactor: Multi-Window design** |

---

## 1. Overview

This document outlines the technical requirements for a new cross-platform desktop log watching utility. The application will be built using **Python** and the **PySide6 (Qt)** GUI toolkit.

This design (v3.0) specifies a **multi-window application**. A simple main window acts as a control panel for adding logs and managing the session. Each tracked log file is opened and tailed in its own separate, new window.

## 2. Target Platform & Technology

* **Language:** Python 3.13+
* **UI Toolkit:** PySide6 6.10.0
* **Target Platforms:** Windows, macOS, Linux

---

## 3. UI/UX Requirements

The application now consists of two primary window types: the Main Control Window and one or more Log Viewer Windows.

### 3.1. Main Control Window

This is the primary `QMainWindow` that opens on application start. It is a simple, two-row layout.

* **Layout:** A central `QWidget` with a `QVBoxLayout`.
* **Row 1: Control Bar**
    * A `QFrame` (to act as a "well") with `setFrameShape(QFrame.Shape.StyledPanel)`.
    * **Layout:** A `QHBoxLayout`.
    * **Contents:**
        * `QLineEdit` (Input Box):
            * `setPlaceholderText("Enter path to log file...")`
            * `returnPressed` signal connects to **Log File Adding** logic (see 4.1).
        * `QPushButton` ("Add Log"):
            * `clicked` signal connects to **Log File Adding** logic (see 4.1).
        * `QPushButton` ("Reset Session"):
            * `clicked` signal connects to **Reset Session** logic (see 4.6).
        * `QPushButton` ("Reset Windows"):
            * `clicked` signal connects to **Reset Windows** logic (see 4.6).
* **Row 2: Tracked Logs List**
    * A `QListWidget` that fills the remaining space.
    * This list displays the file paths of all logs currently being tracked.
    * The `itemDoubleClicked` signal connects to the **Log Window Opening** logic (see 4.5).

### 3.2. Log Viewer Window

This is a separate, top-level `QWidget` (or `QMainWindow`). A new instance of this window is created for each log file being viewed.

* **Window Title:** Must be set to the full path or filename of the log file it is tailing.
* **Layout:** A `QVBoxLayout`.
* **Top: View Controls**
    * A `QHBoxLayout` containing control buttons:
        * `QPushButton` ("Pause"): A checkable button (`setCheckable(True)`).
        * `QPushButton` ("Clear"): Clears the text view.
* **Center: Log Content**
    * A `QPlainTextEdit` that fills the remaining space.
    * Must be read-only (`setReadOnly(True)`).
    * This widget displays the tailed log output.

---

## 4. Functional Requirements

### 4.1. Log File Adding

1.  When a user provides a path via the **Main Control Window** and presses Enter or clicks "Add Log":
2.  The application must **clean and validate** the input path (e.g., `pathlib.Path`).
3.  The application must check file system **permissions** (e.g., `os.access(path, os.R_OK)`).
    * If permissions are not available, display a **dialog error** (`QMessageBox.critical()`).
4.  If the path is valid and not already in the list, add the log file path as an item to the `QListWidget`.
5.  Trigger the **File State Management** logic (see 4.2) for this new file.

### 4.2. File State Management

The application must use a file system watcher library (e.g., **`watchdog`**) to manage file states robustly. This must run in a separate `QThread` for each tracked file.

* **State 1: Non-Existent File**
    1.  **Action:** The file path is valid, but the file does not exist.
    2.  **Behavior:** The application must establish a watch on the **parent directory**.
    3.  Listen for `on_created` events.
    4.  If a created file matches the target, transition to **State 2**.

* **State 2: Exists (Tailing)**
    1.  **Action:** The file exists (or has just been created).
    2.  **Behavior:** The application must:
        * Open the file for reading and seek to the end (`file.seek(0, 2)`).
        * Begin tailing the file.
        * If a **Log Viewer Window** (see 3.2) for this file is open, emit new lines via **Qt signals** to it.
        * Establish a watch on the file for `on_deleted` or `on_moved` events.
    3.  If a `deleted` or `moved` event is detected, transition to **State 3**.

* **State 3: Exists and Deleted/Moved**
    1.  **Action:** The file being tailed is removed or moved.
    2.  **Behavior:** The application must:
        * Close any open file handles.
        * Emit a signal to the corresponding **Log Viewer Window** to display a message (e.g., "File removed, watching for creation...").
        * Transition to **State 1**.

### 4.3. Log Tailing & Display

* Tailing must be performed in a **`QThread`** for each active file.
* A central manager (e.g., in the Main Window) will hold references to all active `LogViewerWindow` instances.
* The tailing thread will emit a signal with new lines. The central manager will route this signal to the correct `LogViewerWindow` instance, if one is open.
* The receiving slot in the `LogViewerWindow` appends text to its `QPlainTextEdit`.
* The `QPlainTextEdit` must automatically scroll to the bottom (`moveCursor(QTextCursor.MoveOperation.End)`).

### 4.4. Log View Controls (in Log Viewer Window)

* **Pause Button (Checkable):**
    * When checked ("Paused"), the UI slot **stops appending** new lines.
    * The background `QThread` **must continue tailing** and buffer the lines.
    * When unchecked ("Unpaused"), the thread emits a signal with all buffered lines, which are then flushed to the UI.
* **Clear Button:**
    * `OnTapped`, this button must call `QPlainTextEdit.clear()` on its `QPlainTextEdit`.

### 4.5. Log Window Opening

1.  When a user **double-clicks** an item in the `QListWidget` (in the Main Control Window):
2.  The application must check if a `LogViewerWindow` for this file path is already open.
    * **If Yes:** Bring that existing window to the front (`raise_()`, `activateWindow()`).
    * **If No:**
        1.  Create a new `LogViewerWindow` instance.
        2.  Store a reference to this instance (e.g., in a `dict` mapping `file_path -> window_instance`).
        3.  Show the new window.
        4.  The tailing thread's signals (see 4.3) will now be connected to this new window's slots.
        5.  The application should immediately read and display the *entire* current content of the log file before starting the "tail" from the end.

### 4.6. Session & Window Management (in Main Control Window)

* **Reset Session Button:**
    1.  Stop all active tailing `QThread`s.
    2.  Close all open `LogViewerWindow` instances.
    3.  Clear the `QListWidget` in the Main Control Window.
    4.  Clear all internal references to log files and window instances.
* **Reset Windows Button:**
    1.  Iterate through all open `LogViewerWindow` instances.
    2.  Programmatically re-position and re-size them into a "tiled" or "cascaded" layout on the screen (e.g., using `move()` and `resize()` in a loop).

---

## 5. Non-Functional Requirements

* **Performance:** File I/O and tailing must be highly efficient and non-blocking.
* **Error Handling:** All file operations must be wrapped in `try...except` blocks and present user-facing errors via **PySide6/Qt dialogs (e.g., `QMessageBox`)**.
* **Concurrency:** Use **`QThread` and Qt's signals/slots mechanism** to manage concurrent tailing operations and UI updates safely.
* **State Management:** The application must maintain a clean state, tracking which threads and windows are open and ensuring they are all properly closed on exit or session reset.

---

## 6. Developer Guidelines

* All code must adhere to the standards and practices defined in **`Docs/CodingGuidelines.md`**.
* All new classes, methods, and complex logic must be documented in accordance with **Python's documentation standards (e.g., Google-style docstrings)**.