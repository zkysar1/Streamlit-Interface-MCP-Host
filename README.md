# Streamlit-Interface-MCP-Host

A sophisticated web-based chat interface for the Agents-MCP-Host backend, featuring real-time SSE streaming, intelligent progress management, and dynamic verbosity control.

## 🎯 Key Features

- **🔄 Real-time Streaming**: See tool calls as they happen via Server-Sent Events
- **📊 Smart Progress Display**: Single updating line instead of spam, with progress bars for multi-step operations
- **🎚️ Dynamic Verbosity Control**: Change detail level (Minimal/Normal/Detailed) without losing data
- **💾 Persistent State Management**: Streaming sessions survive page refreshes and reruns
- **🛑 Floating Control Buttons**: Stop buttons that stay with active responses
- **📋 Collapsible Technical Details**: Debugging information available on demand
- **🧹 Automatic Memory Management**: Old streams cleaned up automatically
- **⏱️ Long Operation Handling**: Special messaging after 30 seconds with timeout protection


## Directory Location
```bash
# Windows (WSL)
win_home=$(wslpath -u "$(wslvar USERPROFILE)")
cd $win_home/OneDrive/Zak/SmartNPCs/MCPThink/Streamlit-Interface-MCP-Host/

# Linux/Mac
cd ~/Streamlit-Interface-MCP-Host/
```


## 📋 Prerequisites

- **Python 3.8+** - Check: `python3 --version`
- **Agents-MCP-Host** - Backend must be running on port 8080

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Linux/WSL
python3 -m pip install --user --break-system-packages -r requirements.txt

# Windows
py -m pip install --user -r requirements.txt
```

### 2. Start the Backend First

```bash
# In Agents-MCP-Host directory
java -jar build/libs/Agents-MCP-Host-1.0.0-fat.jar
```

### 3. Launch Streamlit Interface

```bash
# Linux/WSL
python3 -m streamlit run Home.py

# Windows PowerShell
- Laptop
python -m streamlit run "C:\Users\zkysa\OneDrive\Zak\SmartNPCs\MCPThink\Streamlit-Interface-MCP-Host\Home.py"
- amd desktop
py -m streamlit run "C:\Users\Zachary\OneDrive\Zak\SmartNPCs\MCPThink\Streamlit-Interface-MCP-Host\Home.py"
```


The interface will open at `http://localhost:8501`

## 🏗️ Architecture

### Core Components

1. **Home.py** - Main entry point with system stats
2. **pages/BasicChat.py** - Advanced chat interface with:
   - `StreamingSession` class for persistent state
   - `ProgressManager` class for intelligent display
   - Verbosity-based event filtering

### Enhanced Streaming Architecture

```
User Input → process_command() → send_to_backend_streaming()
                ↓                           ↓
         StreamingSession            SSE Event Stream
         (stores all events)         (real-time updates)
                ↓                           ↓
         ProgressManager ← handle_event() ← Event data
         (filters by verbosity)
                ↓
         Update display (st.empty() for in-place updates)
```

### Event Types & Verbosity

| Event Type | Minimal | Normal | Detailed | Description |
|------------|---------|---------|----------|-------------|
| `connected` | ❌ | ❌ | ✅ | Stream connection established |
| `progress` | ❌ | ❌ | ✅ | Detailed progress updates |
| `tool_call_start` | ❌ | ✅ | ✅ | Shows "🔧 Tool Name" |
| `tool_call_complete` | ❌ | ✅ | ✅ | Shows "✓" checkmark |
| `execution_paused` | ✅ | ✅ | ✅ | User interruption |
| `agent_question` | ✅ | ✅ | ✅ | Agent needs input |
| `error` | ✅ | ✅ | ✅ | Error messages with ❌ |
| `final_response` | ✅ | ✅ | ✅ | The actual response |

## 📦 Dependencies

- **streamlit** - Web UI framework
- **requests** - HTTP client for backend communication
- **sseclient-py** - SSE client for streaming responses
- **psutil** - System information display

## 🧪 Testing

### Test SSE Streaming
```bash
python3 test_streaming.py
```

### Test Full Integration
```bash
python3 test_integration.py
```

## 💡 Usage Examples

### Regular Conversation
Type: "Hello, how are you?"
- Backend uses OpenAI (if configured) or fallback response

### Tool Execution with Progress
Type: "Show me all pending orders from California customers with high priority"

**Minimal verbosity shows:**
```
The total revenue for Q3 2023 is $12,450,000.
```

**Normal verbosity shows:**
```
🔧 Analyze Query
✓ 🔧 Match Schema
✓ 🔧 Generate Sql
✓ 🔧 Execute Query
✓ 

✅ Completed in 15.3s • Used 4 tools
---
[Results displayed here]
```

**Detailed verbosity shows:**
All of the above plus real-time progress updates, SQL queries, and technical details in expandable section.

### Verbosity Control
Use the sidebar slider to adjust detail level during streaming:
- **Minimal**: Only final responses and errors
- **Normal**: Tool executions and completions
- **Detailed**: All progress events and technical information

### Stop Functionality
- Click the 🛑 Stop button to interrupt long operations
- Button appears at the bottom of active responses
- Sends interrupt signal to backend

## 🔧 Configuration

### Backend URL
The backend URL is configured in `pages/BasicChat.py`:
```python
url = "http://localhost:8080/host/v1/conversations"
```

### Session State
Conversation history is maintained in Streamlit's session state with roles:
- **System**: Initial instructions to the assistant
- **User**: User messages
- **Assistant**: AI responses

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Backend server not running" | Start Agents-MCP-Host first on port 8080 |
| No streaming updates | Ensure `sseclient-py` is installed |
| Response disappears on slider change | Fixed in latest version - uses StreamingSession persistence |
| AttributeError on .get() | Fixed - added None checks in handle_event() |
| Duplicate stop buttons | Fixed - uses message_id instead of index for keys |
| Memory growth | Fixed - automatic cleanup of old streams (max 20) |
| Stuck "Streaming..." | Fixed - 10-minute timeout for stale streams |
| Connection drops | Check firewall/proxy settings for SSE |
| Port already in use | Change port: `streamlit run Home.py --server.port 8502` |

### Debug Mode
Enable debug prints by uncommenting lines in BasicChat.py:
- Line 286 in `send_to_backend_streaming()` for SSE events
- Add prints in `handle_event()` for event processing

## 📁 Directory Structure

```
Streamlit-Interface-MCP-Host/
├── Home.py                 # Main entry point with system stats
├── pages/
│   └── BasicChat.py       # Advanced chat interface with:
│                          #   - StreamingSession (persistent state)
│                          #   - ProgressManager (smart display)
│                          #   - Event filtering by verbosity
├── requirements.txt        # Python dependencies
├── test_streaming.py       # SSE test script
├── test_integration.py     # Integration test script
├── CLAUDE.md              # Detailed AI agent documentation
├── README.md              # This file
└── .claude/               # Task-specific onboarding docs
```

## 🚀 Recent Improvements (December 2024)

### UI/UX Enhancements
- **Smart Progress Display**: Single updating line with progress bars
- **Verbosity Persistence**: Change detail level without losing data
- **Floating Controls**: Stop buttons stay with active responses
- **Collapsible Details**: Technical information on demand

### Technical Improvements
- **StreamingSession Class**: Persistent state across Streamlit reruns
- **Memory Management**: Automatic cleanup with 20-stream limit
- **Error Resilience**: None checks prevent AttributeError crashes
- **Unique Keys**: Message IDs prevent button conflicts
- **Timeout Protection**: 10-minute limit for stale streams

### Bug Fixes
- Fixed verbosity slider data loss issue
- Fixed memory leak from unlimited stream storage
- Fixed error formatting consistency
- Fixed button key collisions
- Added proper None data handling

## 🔗 Related Projects

- [Agents-MCP-Host](../Agents-MCP-Host) - Backend server with MCP tool orchestration
- [Model Context Protocol](https://modelcontextprotocol.io) - MCP specification

## 📄 License

MIT License - See LICENSE file for details