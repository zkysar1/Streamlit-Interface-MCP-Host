# Streamlit-Interface-MCP-Host

A modern Streamlit chat interface that connects to the Agents-MCP-Host backend, featuring real-time SSE streaming for transparent tool call notifications.

## 🎯 Key Features

- **🔄 Real-time Streaming**: See tool calls as they happen via Server-Sent Events
- **🔧 Tool Notifications**: Visual indicators for tool execution (🔧 starting, ✓ completed)
- **💬 Progressive Display**: Messages appear as they're being processed
- **🚀 No API Keys Required**: Backend handles all AI/LLM interactions
- **📊 System Monitoring**: Built-in CPU, memory, and disk usage display

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
python -m streamlit run "C:\Users\zkysa\OneDrive\Zak\SmartNPCs\MCPThink\Streamlit-Interface-MCP-Host\Home.py"
```

The interface will open at `http://localhost:8501`

## 🏗️ Architecture

### Components

1. **Home.py** - Main entry point with system stats
2. **pages/BasicChat.py** - Chat interface with SSE streaming

### SSE Streaming Flow

```
User Input → Streamlit UI → HTTP POST (Accept: text/event-stream)
                ↓
        Agents-MCP-Host Backend
                ↓
    SSE Events (tool_call_start, tool_call_complete, final_response)
                ↓
        Progressive Display in UI
```

### Event Types

- `tool_call_start` - Shows "🔧 Calling tool: [tool_name]..."
- `tool_call_complete` - Shows "✓ Tool completed: [tool_name]"
- `final_response` - Displays the actual response
- `error` - Shows error messages with ❌ indicator

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

### Tool Execution
Type: "Calculate 42 plus 58"
- See: 🔧 Calling tool: calculator__add...
- See: ✓ Tool completed: calculator__add
- See: Result: 100.0

### Available Tool Triggers
- **Calculator**: "calculate", "add", "subtract", "multiply", "divide"
- **Weather**: "weather", "forecast", "temperature"
- **Database**: "query", "database", "insert", "update", "delete"
- **Files**: "file", "read file", "write file", "list files"

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
| Connection drops | Check firewall/proxy settings for SSE |
| Port already in use | Change Streamlit port: `streamlit run Home.py --server.port 8502` |

## 📁 Directory Structure

```
Streamlit-Interface-MCP-Host/
├── Home.py                 # Main entry point
├── pages/
│   └── BasicChat.py       # Chat interface with SSE
├── requirements.txt        # Python dependencies
├── test_streaming.py       # SSE test script
├── test_integration.py     # Integration test script
├── CLAUDE.md              # AI agent documentation
└── README.md              # This file
```

## 🔗 Related Projects

- [Agents-MCP-Host](../Agents-MCP-Host) - Backend server with MCP tool orchestration
- [Model Context Protocol](https://modelcontextprotocol.io) - MCP specification

## 📄 License

MIT License - See LICENSE file for details