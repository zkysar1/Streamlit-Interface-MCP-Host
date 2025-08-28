# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive Streamlit-based interface for the Agents-MCP-Host backend API. The application provides multiple pages for monitoring, managing, and interacting with the MCP (Model Context Protocol) system, including real-time dashboards, host management, session monitoring, tool exploration, and an enhanced chat interface with SSE streaming.

## Quick Start

```bash
# From WSL/Linux
export PATH="$HOME/.local/bin:$PATH"
python3 -m pip install --user --break-system-packages -r requirements.txt
python3 -m streamlit run Home.py

# From Windows
python -m streamlit run Home.py
```

The app runs on http://localhost:8501 and requires the Java backend on port 8080.

## Architecture Overview

### Core Components

1. **Home.py**: Entry point with system stats display

### Pages

1. **pages/1_System_Dashboard.py**: Real-time system monitoring
   - Health status, active sessions, uptime metrics
   - Database connection status
   - Host availability overview
   - Critical error alerts
   - Auto-refresh with configurable intervals

2. **pages/2_Host_Manager.py**: Host management interface
   - View all available hosts and their status
   - Select preferred host for conversations
   - Automatic fallback configuration
   - Host capabilities documentation

3. **pages/3_Session_Monitor.py**: Session tracking and management
   - Monitor active streaming sessions
   - Interrupt/cancel sessions
   - Submit session feedback
   - Session analytics and history

4. **pages/4_MCP_Tools.py**: MCP tools and clients explorer
   - Browse available MCP tools with schemas
   - View connected MCP clients
   - Search and filter tools
   - MCP system documentation

5. **pages/5_Enhanced_Chat.py**: Enhanced chat interface
   - Host selection per conversation
   - Session ID tracking and display
   - Real-time progress indicators
   - In-chat feedback buttons
   - Interrupt capability

6. **pages/AllChat.py**: Original chat interface with advanced features:
   - Persistent streaming sessions across reruns
   - Dynamic verbosity control (Minimal/Normal/Detailed)
   - Smart progress display with in-place updates
   - Floating control buttons within messages
   - Collapsible technical details

### Utility Modules

1. **utils/api_client.py**: Centralized API client
   - All endpoint implementations
   - SSE streaming parser
   - Error handling and retries
   - Helper methods for formatting

2. **utils/ui_components.py**: Reusable UI components
   - Status badges and indicators
   - Refresh controls
   - Metric cards
   - Error displays
   - Expandable JSON viewers

### API Endpoints Coverage

The application interfaces with all 13 endpoints from ConversationStreaming.java:

| Endpoint | Method | Page | Purpose |
|----------|--------|------|---------|
| `/` | GET | (API only) | Welcome page |
| `/health` | GET | System Dashboard | Health check |
| `/status` | GET | System Dashboard | Comprehensive status |
| `/hosts/status` | GET | System Dashboard, Host Manager | Host availability |
| `/conversations` | POST | Enhanced Chat | Main conversation (streaming) |
| `/conversations/streaming` | POST | Enhanced Chat | Explicit streaming |
| `/conversations/{id}` | DELETE | Session Monitor | Cancel session |
| `/conversations/{id}/interrupt` | POST | Session Monitor, Enhanced Chat | Interrupt session |
| `/conversations/{id}/feedback` | POST | Session Monitor, Enhanced Chat | Submit feedback |
| `/conversations/{id}/status` | GET | Session Monitor | Session status |
| `/mcp/status` | GET | MCP Tools | MCP system status |
| `/mcp/tools` | GET | MCP Tools | Available tools list |
| `/mcp/clients` | GET | MCP Tools | Connected clients |

### Key Classes (from AllChat.py)

#### StreamingSession (lines 19-82)
Manages persistent streaming state across Streamlit reruns:
- Stores all events for replay with different verbosity
- Tracks completed tools and current phase
- Handles timeout detection (10 min default)
- Maintains error state

#### ProgressManager (lines 84-232)
Handles intelligent progress display:
- Single updating line instead of spam
- Long-running operation detection (30s threshold)
- Progress bar when step info available
- Safe handling of None data

### Critical Implementation Details

#### State Persistence Strategy
```python
# Each message gets a unique ID linking to its streaming session
message_id = str(uuid.uuid4())
st.session_state.active_streams[message_id] = StreamingSession(message_id)

# Messages store their ID for rebuilding
st.session_state.messages.append({
    "role": "Assistant",
    "content": full_response,
    "message_id": message_id  # Key for persistence!
})
```

#### Verbosity Slider Fix
The app rebuilds displays from stored events when verbosity changes:
1. All events stored in StreamingSession.events
2. get_display_events() filters based on current verbosity
3. rebuild_response_display() reconstructs the UI
4. No loss of data during slider changes!

#### Memory Management
- Max 20 active streams (older ones removed)
- 5-minute cleanup for inactive streams
- 10-minute timeout for stuck streams
- Automatic marking as stale with is_stale() method

### Event Types and Display Logic

| Event Type | Minimal | Normal | Detailed | Notes |
|------------|---------|---------|----------|-------|
| connected | ❌ | ❌ | ✅ | Stream ID only |
| progress | ❌ | ❌ | ✅ | All progress events |
| tool_call_start | ❌ | ✅ | ✅ | Shows tool name |
| tool_call_complete | ❌ | ✅ | ✅ | Just checkmark |
| execution_paused | ✅ | ✅ | ✅ | Always shown |
| agent_question | ✅ | ✅ | ✅ | User interaction |
| error | ✅ | ✅ | ✅ | Always prominent |
| final | ✅ | ✅ | ✅ | Main content |

### SSE Streaming Architecture

```
User Input → process_command() → send_to_backend_streaming()
                ↓                           ↓
         StreamingSession            SSE Event Stream
                ↓                           ↓
         Store all events          Parse and yield events
                ↓                           ↓
         ProgressManager ← handle_event() ← Event data
                ↓
         Update display (in-place)
```

### Recent Improvements (December 2024)

1. **Fixed AttributeError**: Added None checks throughout handle_event()
2. **Memory leak prevention**: Added stream limits and cleanup
3. **Consistent error formatting**: Fixed rebuild_response_display returns
4. **Code deduplication**: Created show_technical_details() helper
5. **Button key fixes**: Use message_id instead of index
6. **Stale stream handling**: Auto-timeout after 10 minutes

## New Features Added (December 2024)

1. **Comprehensive Dashboard System**: Full visibility into MCP system health
2. **Multi-Host Support**: Choose between different processing hosts
3. **Session Management**: Track, interrupt, and manage active sessions
4. **Tool Discovery**: Browse and understand available MCP tools
5. **Enhanced Chat**: Improved chat with host selection and feedback
6. **Centralized API Client**: Reusable client for all endpoints
7. **Shared UI Components**: Consistent design across all pages

## Common Development Tasks

### Adding a New Event Type
1. Add to StreamingSession.add_event() for state updates
2. Add to ProgressManager.handle_event() for display
3. Update important_events set if always visible
4. Add to get_display_events() filtering logic

### Modifying Progress Display
- Edit update_progress() in ProgressManager
- The progress_placeholder uses st.empty() for in-place updates
- Check elapsed time for long-running detection

### Debugging Streaming Issues
```python
# Enable debug prints in send_to_backend_streaming()
print(f"[DEBUG] Event: {current_event}, Data: {data_str}")

# Check streaming session state
print(f"Session {message_id}: active={session.is_active}, events={len(session.events)}")
```

## Testing Scenarios

### Manual Testing Checklist
- [ ] Start a long query, change verbosity mid-stream
- [ ] Multiple concurrent messages with different verbosity
- [ ] Error handling with backend down
- [ ] Stop button during active streaming
- [ ] Page refresh during streaming
- [ ] 20+ messages to test cleanup

### Edge Cases to Test
1. **Verbosity changes**: Should rebuild without data loss
2. **Timeout handling**: 10-minute streams should auto-stop
3. **Memory cleanup**: Old streams should be removed
4. **Button conflicts**: Each stop button should be unique
5. **None data**: All event handlers should handle None

## Troubleshooting Guide

| Issue | Cause | Solution |
|-------|-------|----------|
| AttributeError on .get() | None data passed to event handlers | Check isinstance(data, dict) first |
| Response disappears | Streamlit rerun without state | Use StreamingSession for persistence |
| Duplicate stop buttons | Key collision with index | Use message_id for keys |
| Memory growth | No stream cleanup | Check cleanup logic runs |
| Stuck "Streaming..." | No final event | Check is_stale() timeout |

## Performance Considerations

- Each StreamingSession stores all events (memory grows with conversation length)
- Technical details show last 20 events only (performance cap)
- Progress updates use st.empty() for efficiency
- Verbosity checks prevent unnecessary processing

## Future Enhancements

1. **Event compression**: Store only essential data after completion
2. **Pagination**: For very long conversations
3. **Export functionality**: Save chat with full event history
4. **Custom themes**: Based on verbosity level
5. **WebSocket upgrade**: Replace SSE for bidirectional communication