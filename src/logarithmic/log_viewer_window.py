"""Log Viewer Window - displays tailed log content."""

import logging
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtGui import QMoveEvent
from PySide6.QtGui import QResizeEvent
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from logarithmic.fonts import get_font_manager

logger = logging.getLogger(__name__)


class LogViewerWindow(QWidget):
    """A separate window that displays the content of a single log file.
    
    This window shows the tailed output of a log file with controls to
    pause/resume tailing and clear the display.
    
    Implements the LogSubscriber protocol to receive log events from LogManager.
    """

    def __init__(self, file_path: Path, parent: QWidget | None = None) -> None:
        """Initialize the log viewer window.
        
        Args:
            file_path: Path to the log file
            parent: Parent widget
        """
        super().__init__(parent)
        self.file_path = file_path
        self._path_str = str(file_path)
        self._is_paused = False
        self._position_changed_callback: Callable[[int, int, int, int], None] | None = None
        self._last_saved_position: tuple[int, int, int, int] | None = None
        self._is_live_mode = True  # Auto-scroll enabled by default
        self._user_scrolled = False  # Track if user manually scrolled
        self._line_count = 0  # Track number of lines displayed
        self._current_file_name = str(file_path)  # Current file being displayed
        self._restart_count = 0  # Track number of file switches (for wildcards)
        self._is_wildcard = '*' in str(file_path) or '?' in str(file_path)
        self._fonts = get_font_manager()
        self._set_default_size_callback: Callable[[int, int], None] | None = None
        self._get_other_windows_callback: Callable[[], list] | None = None
        self._snap_threshold = 20  # pixels - distance to trigger snap
        
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.resize(800, 600)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Top: Controls
        controls_layout = QHBoxLayout()
        
        # Go Live button (hidden by default, shown when in scroll mode)
        self.go_live_button = QPushButton("Go Live")
        self.go_live_button.setFont(self._fonts.get_ui_font(10, bold=True))
        self.go_live_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.go_live_button.clicked.connect(self._on_go_live_clicked)
        self.go_live_button.hide()  # Hidden by default (in live mode)
        controls_layout.addWidget(self.go_live_button)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setFont(self._fonts.get_ui_font(10))
        self.pause_button.setCheckable(True)
        self.pause_button.toggled.connect(self._on_pause_clicked)
        controls_layout.addWidget(self.pause_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.setFont(self._fonts.get_ui_font(10))
        self.clear_button.clicked.connect(self._on_clear_clicked)
        controls_layout.addWidget(self.clear_button)
        
        # Set Default Size button
        set_size_button = QPushButton("Set Default Size")
        set_size_button.setFont(self._fonts.get_ui_font(10))
        set_size_button.setToolTip("Set the current window size as the default for all new log windows")
        set_size_button.clicked.connect(self._on_set_default_size_clicked)
        controls_layout.addWidget(set_size_button)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Center: Log Content
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Use Red Hat Mono for log content
        self.text_edit.setFont(self._fonts.get_mono_font(9))
        
        # Connect scroll bar to detect user scrolling
        scrollbar = self.text_edit.verticalScrollBar()
        scrollbar.valueChanged.connect(self._on_scroll_changed)
        
        layout.addWidget(self.text_edit)
        
        # Bottom: Status Bar
        self.status_bar = QLabel()
        self.status_bar.setFont(self._fonts.get_ui_font(10))
        self.status_bar.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                color: #cccccc;
                padding: 5px;
                border-top: 1px solid #555555;
            }
        """)
        self.status_bar.setTextFormat(Qt.TextFormat.PlainText)
        self._update_status_bar()
        layout.addWidget(self.status_bar)
        
    def append_text(self, text: str) -> None:
        """Append new text to the log view.
        
        Args:
            text: Text content to append
        """
        logger.debug(f"append_text called with {len(text)} chars, paused={self._is_paused}, live_mode={self._is_live_mode}")
        if not self._is_paused:
            # Move cursor to end and insert text (better than appendPlainText for large content)
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(text)
            self.text_edit.setTextCursor(cursor)
            
            # Update line count
            self._line_count += text.count('\n')
            self._update_status_bar()
            
            # Auto-scroll to bottom only if in live mode
            if self._is_live_mode:
                self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
            
    def set_status_message(self, message: str) -> None:
        """Display a status message in the log view.
        
        Args:
            message: Status message to display
        """
        self.text_edit.appendPlainText(f"\n[{message}]\n")
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
        
    def is_paused(self) -> bool:
        """Check if the viewer is currently paused.
        
        Returns:
            True if paused, False otherwise
        """
        return self._is_paused
        
    def _on_pause_clicked(self, checked: bool) -> None:
        """Handle pause button click.
        
        Args:
            checked: True if button is checked (paused)
        """
        self._is_paused = checked
        if checked:
            self.pause_button.setText("Resume")
        else:
            self.pause_button.setText("Pause")
        self._update_status_bar()
            
    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        self.text_edit.clear()
        self._line_count = 0
        self._update_status_bar()
        
    def _on_scroll_changed(self, value: int) -> None:
        """Handle scroll bar value change.
        
        Detects when user scrolls up (away from bottom) and switches to scroll mode.
        
        Args:
            value: Current scroll bar value
        """
        scrollbar = self.text_edit.verticalScrollBar()
        
        # Check if we're at the bottom (within 10 pixels)
        at_bottom = value >= scrollbar.maximum() - 10
        
        if not at_bottom and self._is_live_mode:
            # User scrolled up, switch to scroll mode
            self._is_live_mode = False
            self.go_live_button.show()
            self._update_status_bar()
            logger.info(f"Switched to scroll mode for {self._path_str}")
        elif at_bottom and not self._is_live_mode:
            # User scrolled to bottom, could auto-switch back to live mode
            # But we'll require explicit "Go Live" button click for better UX
            pass
            
    def _on_go_live_clicked(self) -> None:
        """Handle Go Live button click.
        
        Switches back to live mode and scrolls to bottom.
        """
        self._is_live_mode = True
        self.go_live_button.hide()
        self._update_status_bar()
        
        # Scroll to bottom
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
        
        logger.info(f"Switched to live mode for {self._path_str}")
        
    def set_default_size_callback(self, callback: Callable[[int, int], None]) -> None:
        """Set callback for when user sets default size.
        
        Args:
            callback: Function to call with (width, height)
        """
        self._set_default_size_callback = callback
    
    def set_other_windows_callback(self, callback: Callable[[], list]) -> None:
        """Set callback to get list of other windows for snapping.
        
        Args:
            callback: Function that returns list of other LogViewerWindow instances
        """
        self._get_other_windows_callback = callback
    
    def _on_set_default_size_clicked(self) -> None:
        """Handle Set Default Size button click."""
        width = self.width()
        height = self.height()
        
        if self._set_default_size_callback:
            self._set_default_size_callback(width, height)
            logger.info(f"Set default size to {width}x{height}")
    
    def set_position_changed_callback(self, callback: Callable[[int, int, int, int], None]) -> None:
        """Set callback for when window position/size changes.
        
        Args:
            callback: Function that takes (x, y, width, height)
        """
        self._position_changed_callback = callback
        
    def moveEvent(self, event: QMoveEvent) -> None:
        """Handle window move event with auto-snapping.
        
        Args:
            event: Move event
        """
        # Auto-snap to other windows if callback is set
        if self._get_other_windows_callback:
            other_windows = self._get_other_windows_callback()
            if other_windows:
                snapped_pos = self._calculate_snap_position(other_windows)
                if snapped_pos:
                    # Move to snapped position
                    super().moveEvent(event)
                    self.move(snapped_pos[0], snapped_pos[1])
                    self._save_position_if_changed()
                    return
        
        super().moveEvent(event)
        self._save_position_if_changed()
            
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle window resize event.
        
        Args:
            event: Resize event
        """
        super().resizeEvent(event)
        self._save_position_if_changed()
        
    def _calculate_snap_position(self, other_windows: list) -> tuple[int, int] | None:
        """Calculate snapped position if close to another window.
        
        Args:
            other_windows: List of other LogViewerWindow instances
            
        Returns:
            Tuple of (x, y) if should snap, None otherwise
        """
        my_rect = self.geometry()
        my_frame = self.frameGeometry()  # Includes title bar
        my_x = my_rect.x()
        my_y = my_rect.y()
        my_width = my_rect.width()
        my_height = my_rect.height()
        
        # Calculate title bar height (frame height - content height)
        title_bar_height = my_frame.height() - my_rect.height()
        
        threshold = self._snap_threshold
        
        for other in other_windows:
            other_rect = other.geometry()
            other_frame = other.frameGeometry()
            other_x = other_rect.x()
            other_y = other_rect.y()
            other_width = other_rect.width()
            other_height = other_rect.height()
            
            # Check for snap to right edge of other window
            if abs((other_x + other_width) - my_x) < threshold:
                # Check if vertically aligned enough
                if not (my_y + my_height < other_y or my_y > other_y + other_height):
                    return (other_x + other_width, other_y)
            
            # Check for snap to left edge of other window
            if abs(other_x - (my_x + my_width)) < threshold:
                # Check if vertically aligned enough
                if not (my_y + my_height < other_y or my_y > other_y + other_height):
                    return (other_x - my_width, other_y)
            
            # Check for snap to bottom edge of other window
            if abs((other_y + other_height) - my_y) < threshold:
                # Check if horizontally aligned enough
                if not (my_x + my_width < other_x or my_x > other_x + other_width):
                    return (other_x, other_y + other_height)
            
            # Check for snap to top edge of other window (account for title bar)
            if abs(other_y - (my_y + my_height)) < threshold:
                # Check if horizontally aligned enough
                if not (my_x + my_width < other_x or my_x > other_x + other_width):
                    # Snap above, but leave room for the title bar
                    return (other_x, other_y - my_height - title_bar_height)
        
        return None
    
    def _save_position_if_changed(self) -> None:
        """Save position only if it has changed significantly."""
        if self._position_changed_callback:
            pos = self.pos()
            size = self.size()
            current = (pos.x(), pos.y(), size.width(), size.height())
            
            # Only save if position changed by more than 5 pixels or size changed
            if self._last_saved_position is None:
                self._position_changed_callback(*current)
                self._last_saved_position = current
            else:
                dx = abs(current[0] - self._last_saved_position[0])
                dy = abs(current[1] - self._last_saved_position[1])
                dw = abs(current[2] - self._last_saved_position[2])
                dh = abs(current[3] - self._last_saved_position[3])
                
                if dx > 5 or dy > 5 or dw > 0 or dh > 0:
                    self._position_changed_callback(*current)
                    self._last_saved_position = current
            
    # LogSubscriber protocol methods
    
    def on_log_content(self, path: str, content: str) -> None:
        """Called when new log content is available.
        
        Args:
            path: Log file path
            content: New content to append
        """
        if path == self._path_str:
            if not self._is_paused:
                self.append_text(content)
                logger.debug(f"Appended {len(content)} chars to viewer for {path}")
            else:
                logger.debug(f"Content received but viewer is paused for {path}")
    
    def on_log_cleared(self, path: str) -> None:
        """Called when log buffer is cleared.
        
        Args:
            path: Log file path
        """
        if path == self._path_str:
            self.text_edit.clear()
            self._line_count = 0
            self._update_status_bar()
            logger.info(f"Cleared viewer for {path}")
    
    def on_stream_interrupted(self, path: str, reason: str) -> None:
        """Called when the log stream is interrupted.
        
        Args:
            path: Log file path
            reason: Reason for interruption
        """
        if path == self._path_str:
            # Extract new filename from reason first
            if "Initial file:" in reason:
                # Initial file for wildcard - just set the name, don't show separator
                parts = reason.split("Initial file:")
                if len(parts) == 2:
                    new_filename = parts[1].strip()
                    if '\\' in new_filename or '/' in new_filename:
                        self._current_file_name = Path(new_filename).name
                    else:
                        self._current_file_name = new_filename
                    logger.info(f"Initial wildcard file: {self._current_file_name}")
                self._update_status_bar()
                return  # Don't show separator for initial file
            
            # Show separator for actual interruptions
            separator = (
                "\n"
                "═" * 70 + "\n"
                f"║  Stream Interrupted: {reason}\n"
                f"║  Waiting for file to be recreated...\n"
                "═" * 70 + "\n"
            )
            self.text_edit.appendPlainText(separator)
            self._line_count += separator.count('\n')
            
            # Extract new filename from reason
            if "Switching from" in reason and " to " in reason:
                # File switch - increment restart count
                parts = reason.split(" to ")
                if len(parts) == 2:
                    new_filename = parts[1].strip()
                    # Extract just the filename if it's a full path
                    if '\\' in new_filename or '/' in new_filename:
                        self._current_file_name = Path(new_filename).name
                    else:
                        self._current_file_name = new_filename
                    # Increment restart count for wildcard patterns
                    if self._is_wildcard:
                        self._restart_count += 1
                        logger.info(f"Wildcard restart #{self._restart_count}: switched to {self._current_file_name}")
            
            self._update_status_bar()
            if self._is_live_mode:
                self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
            logger.info(f"Displayed stream interruption for {path}: {reason}")
    
    def on_stream_resumed(self, path: str) -> None:
        """Called when the log stream resumes.
        
        Args:
            path: Log file path
        """
        if path == self._path_str:
            separator = (
                "\n"
                "═" * 70 + "\n"
                "║  Stream Resumed - File Recreated\n"
                "═" * 70 + "\n"
                "\n"
            )
            self.text_edit.appendPlainText(separator)
            self._line_count += separator.count('\n')
            self._update_status_bar()
            if self._is_live_mode:
                self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
            logger.info(f"Displayed stream resumption for {path}")
    
    def _update_status_bar(self) -> None:
        """Update the status bar with current file information."""
        # Get file size if it exists
        file_size_str = "N/A"
        try:
            if Path(self._current_file_name).exists():
                file_size = Path(self._current_file_name).stat().st_size
                # Format size in human-readable format
                if file_size < 1024:
                    file_size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    file_size_str = f"{file_size / 1024:.1f} KB"
                elif file_size < 1024 * 1024 * 1024:
                    file_size_str = f"{file_size / (1024 * 1024):.1f} MB"
                else:
                    file_size_str = f"{file_size / (1024 * 1024 * 1024):.1f} GB"
        except Exception:
            pass
        
        # Get just the filename (not full path) for display
        display_name = Path(self._current_file_name).name
        
        # Build status text
        mode = "🔴 LIVE" if self._is_live_mode else "⏸ SCROLL"
        pause_status = " [PAUSED]" if self._is_paused else ""
        
        # Add restart count for wildcard patterns
        restart_info = ""
        if self._is_wildcard and self._restart_count > 0:
            restart_info = f"  |  🔄 {self._restart_count} restarts"
        
        status_text = f"📄 {display_name}  |  📊 {self._line_count:,} lines  |  💾 {file_size_str}  |  {mode}{pause_status}{restart_info}"
        
        self.status_bar.setText(status_text)
    
    def flash_window(self) -> None:
        """Flash the window to get user's attention."""
        # Save original window title
        original_title = self.windowTitle()
        
        # Flash by changing title briefly
        self.setWindowTitle(f"⚠️ {original_title} ⚠️")
        
        # Restore after 500ms
        from PySide6.QtCore import QTimer
        QTimer.singleShot(500, lambda: self.setWindowTitle(original_title))
        
        logger.info(f"Flashed window for {self._path_str}")
