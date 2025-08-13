# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Streamlit-based chat interface that connects to the Agents-MCP-Host backend API. The application provides a web-based chat interface with real-time SSE streaming for tool call notifications.

## Key Commands

### Running the Application

From WSL:
```bash
# Ensure pip packages are installed
export PATH="$HOME/.local/bin:$PATH"
python3 -m pip install --user --break-system-packages -r requirements.txt

# Run the application
python3 -m streamlit run Home.py
```

From Windows PowerShell/Command Prompt:
```bash
python -m streamlit run "C:\Users\zkysa\OneDrive\Zak\SmartNPCs\MCPThink\Streamlit-Interface-MCP-Host\Home.py"
```

### Installing Dependencies

In WSL (requires --break-system-packages flag due to system Python):
```bash
export PATH="$HOME/.local/bin:$PATH"
python3 -m pip install --user --break-system-packages -r requirements.txt
```

Required packages:
- `streamlit` - Web UI framework
- `requests` - HTTP client for backend communication
- `sseclient-py` - SSE client for streaming responses
- `psutil` - System information display

## Architecture

### Core Components

1. **Home.py**: Main entry point, displays system statistics (CPU, memory, disk usage)

2. **pages/BasicChat.py**: Chat interface page that:
   - Sends messages to Agents-MCP-Host backend via HTTP
   - Uses SSE streaming for real-time tool notifications
   - Manages conversation history in Streamlit session state
   - Displays progressive updates with `st.write_stream()`

### Key Implementation Details

- **Backend Integration**: Uses `requests` library for HTTP communication with Agents-MCP-Host
- **SSE Streaming**: Uses `sseclient-py` to process Server-Sent Events from backend
- **Session Management**: Chat history stored in `st.session_state.messages` with role-based structure
- **Message Format**: Messages include roles: "System", "User", "Assistant"
- **Streaming Display**: Shows tool call notifications (🔧), completions (✓), and final responses
- **Error Handling**: Graceful fallback when backend is unavailable

### SSE Streaming Flow

1. User sends message
2. Frontend adds `Accept: text/event-stream` header
3. Backend streams events:
   - `tool_call_start` - Shows "🔧 Calling tool..."
   - `tool_call_complete` - Shows "✓ Tool completed"
   - `final_response` - Shows actual response
4. Frontend uses `st.empty()` and `st.markdown()` for progressive display

## Environment Requirements

- **Backend Service**: Agents-MCP-Host must be running on port 8080
- **Python Dependencies**: streamlit, requests, sseclient-py, psutil (see requirements.txt)
- **No API Keys Required**: Backend handles all AI/LLM interactions

## Directory Locations

- Windows WSL: `/mnt/c/Users/zkysa/OneDrive/Zak/SmartNPCs/MCPThink/Streamlit-Interface-MCP-Host/`
- Linux/Mac: `~/ZAK-Agent/`

## Development Notes

- **Main Functions**:
  - `send_to_backend_streaming()` - Handles SSE communication with backend
  - `process_command()` - Orchestrates message processing and streaming
- **Streaming Logic**: The response generator yields chunks that are progressively displayed
- **Backend URL**: Hardcoded to `http://localhost:8080/host/v1/conversations`
- The application runs on port 8501 by default
- Streamlit configuration can be found in `~/.streamlit/config.toml` (if created)

## Testing

```bash
# Test SSE streaming functionality
python3 test_streaming.py

# Test full integration
python3 test_integration.py
```

## Troubleshooting

- **"Backend server not running"**: Start Agents-MCP-Host first
- **No streaming**: Check that `sseclient-py` is installed
- **Events not showing**: Verify Accept header is being sent
- **Connection drops**: Check for proxy/firewall blocking SSE