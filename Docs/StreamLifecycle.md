# Stream Lifecycle Management

## Overview

Logarithmic implements a robust stream lifecycle management system that gracefully handles log file deletion, truncation, and recreation. This is essential for real-world scenarios like application recompiles, log rotation, and server restarts.

## Architecture

### Publisher-Subscriber Pattern

The stream lifecycle uses the same publisher-subscriber pattern as content delivery:

```
FileWatcherThread (Producer)
    ↓ detects file deletion
LogManager (Hub)
    ↓ publishes stream_interrupted event
LogViewerWindow (Subscriber)
    ↓ displays visual separator
```

### Protocol Extension

The `LogSubscriber` protocol defines four lifecycle methods:

```python
class LogSubscriber(Protocol):
    def on_log_content(path: str, content: str) -> None
    def on_log_cleared(path: str) -> None
    def on_stream_interrupted(path: str, reason: str) -> None  # NEW
    def on_stream_resumed(path: str) -> None                   # NEW
```

## Stream States

### State 1: Normal Operation
- File exists and is being tailed
- Content flows to subscribers
- Auto-scroll enabled (if in live mode)

### State 2: Stream Interrupted
- File deleted or truncated
- Visual separator displayed:
```
══════════════════════════════════════════════════════════════════
║  Stream Interrupted: File deleted
║  Waiting for file to be recreated...
══════════════════════════════════════════════════════════════════
```
- FileWatcherThread returns to State 1 (watching for creation)
- Subscribers notified via `on_stream_interrupted()`

### State 3: Stream Resumed
- File recreated
- Visual separator displayed:
```
══════════════════════════════════════════════════════════════════
║  Stream Resumed - File Recreated
══════════════════════════════════════════════════════════════════
```
- FileWatcherThread starts tailing new file
- Subscribers notified via `on_stream_resumed()`
- Content delivery resumes

## Event Flow

### File Deletion

1. **Watchdog detects deletion**
   ```python
   # In _FileTailHandler
   def on_deleted(event):
       if event.src_path == target_file:
           callback()  # -> _on_file_deleted
   ```

2. **FileWatcherThread publishes events**
   ```python
   def _on_file_deleted(self):
       self._log_manager.publish_file_deleted(self._path_key)
       self._log_manager.publish_stream_interrupted(self._path_key, "File deleted")
       self._cleanup()
       self._watch_for_creation()  # Return to State 1
   ```

3. **LogManager notifies subscribers**
   ```python
   def _on_stream_interrupted(self, path: str, reason: str):
       for subscriber in subscribers:
           subscriber.on_stream_interrupted(path, reason)
   ```

4. **LogViewerWindow displays separator**
   ```python
   def on_stream_interrupted(self, path: str, reason: str):
       separator = "═" * 70 + "\n" + f"║  Stream Interrupted: {reason}\n" + ...
       self.text_edit.appendPlainText(separator)
   ```

### File Recreation

1. **Watchdog detects creation**
   ```python
   # In _FileCreationHandler
   def on_created(event):
       if event.src_path == target_file:
           callback()  # -> _on_file_created
   ```

2. **FileWatcherThread publishes events**
   ```python
   def _on_file_created(self):
       self._log_manager.publish_file_created(self._path_key)
       self._log_manager.publish_stream_resumed(self._path_key)
       self._start_tailing()  # Return to State 2
   ```

3. **LogManager notifies subscribers**
   ```python
   def _on_stream_resumed(self, path: str):
       for subscriber in subscribers:
           subscriber.on_stream_resumed(path)
   ```

4. **LogViewerWindow displays separator**
   ```python
   def on_stream_resumed(self, path: str):
       separator = "═" * 70 + "\n" + "║  Stream Resumed - File Recreated\n" + ...
       self.text_edit.appendPlainText(separator)
   ```

## Visual Indicators

### Interrupted Separator
```
══════════════════════════════════════════════════════════════════
║  Stream Interrupted: File deleted
║  Waiting for file to be recreated...
══════════════════════════════════════════════════════════════════
```

### Resumed Separator
```
══════════════════════════════════════════════════════════════════
║  Stream Resumed - File Recreated
══════════════════════════════════════════════════════════════════
```

**Design Rationale:**
- **Box drawing characters (═, ║)**: Visually distinct from log content
- **70 characters wide**: Fits standard terminal width
- **Clear messaging**: Immediately obvious what happened
- **Persistent**: Remains in log history for debugging

## Use Cases

### Application Recompile
```
[app logs...]
══════════════════════════════════════════════════════════════════
║  Stream Interrupted: File deleted
║  Waiting for file to be recreated...
══════════════════════════════════════════════════════════════════
[developer recompiles app]
══════════════════════════════════════════════════════════════════
║  Stream Resumed - File Recreated
══════════════════════════════════════════════════════════════════
[new app logs...]
```

### Log Rotation
```
[old logs...]
══════════════════════════════════════════════════════════════════
║  Stream Interrupted: File deleted
║  Waiting for file to be recreated...
══════════════════════════════════════════════════════════════════
[logrotate truncates file]
══════════════════════════════════════════════════════════════════
║  Stream Resumed - File Recreated
══════════════════════════════════════════════════════════════════
[new logs...]
```

### Server Restart
```
[server shutdown logs...]
══════════════════════════════════════════════════════════════════
║  Stream Interrupted: File deleted
║  Waiting for file to be recreated...
══════════════════════════════════════════════════════════════════
[server starts, creates new log file]
══════════════════════════════════════════════════════════════════
║  Stream Resumed - File Recreated
══════════════════════════════════════════════════════════════════
[server startup logs...]
```

## Plugin Architecture

The stream lifecycle system is designed to support future plugins:

### Current Implementation (File-based)
```python
class FileWatcherThread:
    """Watches filesystem for changes."""
    def _on_file_deleted(self):
        self._log_manager.publish_stream_interrupted(...)
    
    def _on_file_created(self):
        self._log_manager.publish_stream_resumed(...)
```

### Future Plugin Example (Network-based)
```python
class NetworkLogStream:
    """Streams logs from remote server."""
    def _on_connection_lost(self):
        self._log_manager.publish_stream_interrupted(
            self._stream_id, "Connection lost"
        )
    
    def _on_reconnected(self):
        self._log_manager.publish_stream_resumed(self._stream_id)
```

### Future Plugin Example (Docker-based)
```python
class DockerLogStream:
    """Streams logs from Docker container."""
    def _on_container_stopped(self):
        self._log_manager.publish_stream_interrupted(
            self._container_id, "Container stopped"
        )
    
    def _on_container_started(self):
        self._log_manager.publish_stream_resumed(self._container_id)
```

## Thread Safety

All stream lifecycle events use Qt signals for thread-safe communication:

1. **Producer Thread** (FileWatcherThread): Emits signals
2. **Qt Event Loop** (Main Thread): Queues signals
3. **LogManager** (Main Thread): Processes signals, notifies subscribers
4. **Subscribers** (Main Thread): Update UI

No manual locking required for UI updates!

## Error Handling

### Missing File on Startup
- FileWatcherThread starts in State 1 (watching for creation)
- No interruption event (file never existed)
- Waits silently for file creation

### Rapid Delete/Create Cycles
- Each cycle generates interruption + resumption events
- Visual separators show timeline of events
- No data loss (buffered content preserved)

### Permission Errors
- Caught and reported via `error_occurred` signal
- Does not trigger stream interruption
- User sees error dialog

## Benefits

1. **Clear Timeline**: Visual separators show when restarts happened
2. **No Data Loss**: Buffer preserved across interruptions
3. **Automatic Recovery**: Resumes when file recreated
4. **Extensible**: Plugin architecture for future log sources
5. **Thread-Safe**: Qt signals handle all cross-thread communication
6. **User-Friendly**: Clear visual feedback for all state changes

## Testing

To test stream lifecycle:

1. **Start app and open a log file**
2. **Delete the log file**: See "Stream Interrupted" separator
3. **Recreate the log file**: See "Stream Resumed" separator
4. **Write to new file**: Content appears normally

Example test script:
```bash
# Create test log
echo "Line 1" > test.log

# Open in Logarithmic

# Delete and recreate
rm test.log
sleep 2
echo "Line 2" > test.log

# Should see:
# Line 1
# ══════════════════════════════════════════════════════════════════
# ║  Stream Interrupted: File deleted
# ║  Waiting for file to be recreated...
# ══════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════
# ║  Stream Resumed - File Recreated
# ══════════════════════════════════════════════════════════════════
# Line 2
```
