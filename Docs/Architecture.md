# Logarithmic Architecture

## Overview

Logarithmic uses a **publisher-subscriber pattern** for log content distribution, ensuring clean separation of concerns and efficient content delivery to multiple viewers.

## Core Components

### 1. LogManager (Central Hub)

**Location**: `src/logarithmic/log_manager.py`

**Responsibilities**:
- Maintains `LogBuffer` instances for each tracked log file
- Publishes log events to registered subscribers
- Provides thread-safe communication via Qt signals
- Manages subscriber lifecycle

**Key Features**:
- **LogBuffer**: Circular buffer storing up to 10,000 lines per file
- **Publisher-Subscriber**: Decouples producers (watchers) from consumers (viewers)
- **Automatic Replay**: New subscribers immediately receive current buffer content
- **Thread-Safe**: Uses Qt signals for cross-thread communication

### 2. FileWatcherThread (Producer)

**Location**: `src/logarithmic/file_watcher.py`

**Responsibilities**:
- Watches log files for changes using `watchdog`
- Reads new content as it's written
- Publishes content to `LogManager`
- Manages 3-state file lifecycle (non-existent → exists → deleted)

**Publishing Events**:
- `publish_content(path, content)` - New log lines available
- `publish_file_created(path)` - File was created
- `publish_file_deleted(path)` - File was deleted/moved

### 3. LogViewerWindow (Subscriber)

**Location**: `src/logarithmic/log_viewer_window.py`

**Responsibilities**:
- Displays log content in a text widget
- Implements `LogSubscriber` protocol
- Receives updates from `LogManager`
- Provides pause/clear controls

**Subscriber Methods**:
- `on_log_content(path, content)` - Append new content
- `on_log_cleared(path)` - Clear display

### 4. MainWindow (Orchestrator)

**Location**: `src/logarithmic/main_window.py`

**Responsibilities**:
- Creates and manages `LogManager` instance
- Registers log files with `LogManager`
- Creates `FileWatcherThread` instances
- Creates and subscribes `LogViewerWindow` instances
- Manages session persistence

## Data Flow

```
┌─────────────────┐
│  Log File       │
│  (on disk)      │
└────────┬────────┘
         │
         │ watchdog events
         ▼
┌─────────────────────┐
│ FileWatcherThread   │ (Producer)
│ - Reads new content │
│ - Publishes to      │
│   LogManager        │
└─────────┬───────────┘
          │
          │ publish_content(path, content)
          ▼
┌─────────────────────────────┐
│      LogManager             │ (Hub)
│ ┌─────────────────────────┐ │
│ │ LogBuffer (per file)    │ │
│ │ - Stores last 10k lines │ │
│ │ - Circular buffer       │ │
│ └─────────────────────────┘ │
│                             │
│ Subscribers:                │
│ - LogViewerWindow #1        │
│ - LogViewerWindow #2        │
│ - LogViewerWindow #N        │
└──────────┬──────────────────┘
           │
           │ on_log_content(path, content)
           ▼
┌─────────────────────┐
│ LogViewerWindow     │ (Subscriber)
│ - Displays content  │
│ - Auto-scrolls      │
│ - Pause/Clear       │
└─────────────────────┘
```

## Key Design Patterns

### Publisher-Subscriber Pattern

**Benefits**:
- **Decoupling**: Watchers don't know about viewers
- **Scalability**: Multiple viewers can subscribe to same log
- **Flexibility**: Easy to add new subscriber types
- **Buffering**: New subscribers get historical content

**Implementation**:
```python
# Producer (FileWatcherThread)
self._log_manager.publish_content(path, content)

# Hub (LogManager)
def publish_content(self, path: str, content: str) -> None:
    self.log_content_available.emit(path, content)  # Qt signal
    
def _on_content_available(self, path: str, content: str) -> None:
    buffer.append(content)  # Store in buffer
    for subscriber in self._subscribers[path]:
        subscriber.on_log_content(path, content)  # Notify

# Subscriber (LogViewerWindow)
def on_log_content(self, path: str, content: str) -> None:
    self.append_text(content)  # Display
```

### Protocol-Based Interfaces

**LogSubscriber Protocol**:
```python
class LogSubscriber(Protocol):
    def on_log_content(self, path: str, content: str) -> None: ...
    def on_log_cleared(self, path: str) -> None: ...
```

**Benefits**:
- Type-safe without inheritance
- Duck typing with type checking
- Easy to implement new subscriber types

## Thread Safety

### Qt Signals for Cross-Thread Communication

All cross-thread communication uses Qt signals:

1. **FileWatcherThread → LogManager**: 
   - Runs in separate thread
   - Emits signals that are queued to main thread

2. **LogManager → LogViewerWindow**:
   - Qt signals ensure thread-safe delivery
   - Automatic marshalling to UI thread

### Buffer Access

- All buffer operations happen in the main thread
- Qt signal/slot mechanism handles synchronization
- No manual locking required

## Memory Management

### Circular Buffer (LogBuffer)

- **Default Size**: 10,000 lines per file
- **Behavior**: Oldest lines dropped when full
- **Memory**: ~1MB per 10k lines (average 100 chars/line)

### Cleanup

- Buffers cleared when log unregistered
- Subscribers automatically unsubscribed on window close
- Watchers stopped and cleaned up on session reset

## Session Persistence

**Stored in**: `~/.logarithmic/settings.json`

**Persisted Data**:
- List of tracked log files
- List of open viewer windows
- Window positions and sizes per log file

**Restoration Flow**:
1. Load settings on startup
2. Register logs with `LogManager`
3. Create `FileWatcherThread` for each log
4. Open viewer windows for previously open logs
5. Subscribe viewers to `LogManager`
6. Viewers receive current buffer content

## Error Handling

### FileWatcherThread Errors

- Emits `error_occurred` signal
- Displayed in `QMessageBox` by `MainWindow`
- Thread continues running (doesn't crash)

### LogManager Errors

- Subscriber notification errors caught and logged
- One failing subscriber doesn't affect others
- Errors logged with full traceback

## Performance Considerations

### Efficient Content Distribution

- **Single Read**: File read once by watcher
- **Multiple Delivery**: Content distributed to N subscribers
- **No Duplication**: Content stored once in buffer
- **Lazy Delivery**: Only active subscribers receive updates

### Buffering Strategy

- **Circular Buffer**: O(1) append, bounded memory
- **Immediate Delivery**: No artificial delays
- **Batch Updates**: Multiple lines sent together

## Future Enhancements

### Potential Additions

1. **Filtering Subscribers**: Subscribe to filtered content (regex, level)
2. **Multiple Buffers**: Different retention policies per log
3. **Persistence**: Save buffer to disk for crash recovery
4. **Statistics**: Track bytes/lines per second
5. **Remote Subscribers**: Network-based log viewers

### Extension Points

- New subscriber types (e.g., `LogStatisticsCollector`)
- Custom buffer implementations (e.g., `CompressedLogBuffer`)
- Alternative publishers (e.g., `NetworkLogPublisher`)
