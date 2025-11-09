"""Settings management for persisting application state."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Settings:
    """Manages application settings persistence.
    
    Settings are stored in a JSON file in the user's home directory.
    """

    def __init__(self) -> None:
        """Initialize settings manager."""
        self.settings_dir = Path.home() / ".logarithmic"
        self.settings_file = self.settings_dir / "settings.json"
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load settings from disk."""
        if not self.settings_file.exists():
            logger.info("No settings file found, using defaults")
            self._data = {
                "tracked_logs": [],
                "open_windows": [],
                "window_positions": {},
                "default_window_width": 1000,
                "default_window_height": 800,  # ~40 lines with controls
                "groups": [],  # List of group names
                "log_groups": {}  # path_key -> group_name mapping
            }
            return

        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            logger.info(f"Loaded settings from: {self.settings_file}")
            
            # Ensure all keys exist
            if "open_windows" not in self._data:
                self._data["open_windows"] = []
            if "window_positions" not in self._data:
                self._data["window_positions"] = {}
            if "default_window_width" not in self._data:
                self._data["default_window_width"] = 1000
            if "default_window_height" not in self._data:
                self._data["default_window_height"] = 800
            if "groups" not in self._data:
                self._data["groups"] = []
            if "log_groups" not in self._data:
                self._data["log_groups"] = {}
                
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            self._data = {
                "tracked_logs": [],
                "open_windows": [],
                "window_positions": {}
            }

    def _save(self) -> None:
        """Save settings to disk."""
        try:
            # Create directory if it doesn't exist
            self.settings_dir.mkdir(parents=True, exist_ok=True)

            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            logger.info(f"Saved settings to: {self.settings_file}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def get_tracked_logs(self) -> list[str]:
        """Get list of tracked log file paths.
        
        Returns:
            List of file paths as strings
        """
        return self._data.get("tracked_logs", [])

    def set_tracked_logs(self, paths: list[str]) -> None:
        """Set list of tracked log file paths.
        
        Args:
            paths: List of file paths as strings
        """
        self._data["tracked_logs"] = paths
        self._save()

    def add_tracked_log(self, path: str) -> None:
        """Add a log file path to tracked logs.
        
        Args:
            path: File path as string
        """
        tracked = self.get_tracked_logs()
        if path not in tracked:
            tracked.append(path)
            self.set_tracked_logs(tracked)

    def remove_tracked_log(self, path: str) -> None:
        """Remove a log file path from tracked logs.
        
        Args:
            path: File path as string
        """
        tracked = self.get_tracked_logs()
        if path in tracked:
            tracked.remove(path)
            self.set_tracked_logs(tracked)

    def clear_tracked_logs(self) -> None:
        """Clear all tracked log file paths."""
        self.set_tracked_logs([])
        
    def get_open_windows(self) -> list[str]:
        """Get list of log paths that should have open windows.
        
        Returns:
            List of file paths as strings
        """
        return self._data.get("open_windows", [])
    
    def set_open_windows(self, paths: list[str]) -> None:
        """Set list of log paths that have open windows.
        
        Args:
            paths: List of file paths as strings
        """
        self._data["open_windows"] = paths
        self._save()
        
    def get_window_position(self, path: str) -> dict[str, int] | None:
        """Get window position and size for a log file.
        
        Args:
            path: File path as string
            
        Returns:
            Dict with x, y, width, height or None
        """
        return self._data.get("window_positions", {}).get(path)
    
    def set_window_position(self, path: str, x: int, y: int, width: int, height: int) -> None:
        """Set window position and size for a log file.
        
        Args:
            path: File path as string
            x: X position
            y: Y position
            width: Window width
            height: Window height
        """
        if "window_positions" not in self._data:
            self._data["window_positions"] = {}
        self._data["window_positions"][path] = {
            "x": x,
            "y": y,
            "width": width,
            "height": height
        }
        self._save()
    
    def get_default_window_size(self) -> tuple[int, int]:
        """Get default window size.
        
        Returns:
            Tuple of (width, height)
        """
        width = self._data.get("default_window_width", 1000)
        height = self._data.get("default_window_height", 800)
        return (width, height)
    
    def set_default_window_size(self, width: int, height: int) -> None:
        """Set default window size.
        
        Args:
            width: Window width
            height: Window height
        """
        self._data["default_window_width"] = width
        self._data["default_window_height"] = height
        self._save()
        logger.info(f"Set default window size to {width}x{height}")
    
    def get_groups(self) -> list[str]:
        """Get list of group names.
        
        Returns:
            List of group names
        """
        return self._data.get("groups", [])
    
    def set_groups(self, groups: list[str]) -> None:
        """Set list of group names.
        
        Args:
            groups: List of group names
        """
        self._data["groups"] = groups
        self._save()
    
    def get_log_groups(self) -> dict[str, str]:
        """Get log-to-group assignments.
        
        Returns:
            Dictionary mapping path_key to group_name
        """
        return self._data.get("log_groups", {})
    
    def set_log_groups(self, log_groups: dict[str, str]) -> None:
        """Set log-to-group assignments.
        
        Args:
            log_groups: Dictionary mapping path_key to group_name
        """
        self._data["log_groups"] = log_groups
        self._save()
