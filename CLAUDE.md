# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Streamlit-based chat interface that connects to OpenAI's API (specifically `gpt-4o-mini-2024-07-18`). The application provides a web-based chat interface with session state management.

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
python3 -m pip install --user --break-system-packages openai streamlit psutil
```

## Architecture

### Core Components

1. **Home.py**: Main entry point, displays system statistics (CPU, memory, disk usage)

2. **pages/BasicChat.py**: Chat interface page that:
   - Initializes OpenAI client using `OPENAI_API_KEY` environment variable
   - Manages conversation history in Streamlit session state
   - Converts user messages to OpenAI API format
   - Displays chat messages with role-based formatting

### Key Implementation Details

- **OpenAI Integration**: Uses `@st.cache_resource` decorator to cache the OpenAI client initialization
- **Session Management**: Chat history stored in `st.session_state.messages` with role-based structure
- **Message Format**: Messages include roles: "System", "User", "Assistant"
- **API Model**: Configured to use `gpt-4o-mini-2024-07-18` with max_tokens=400 and temperature=0.2

## Environment Requirements

- **OPENAI_API_KEY**: Must be set as environment variable (available in both Windows and WSL)
- **Python Dependencies**: openai, streamlit, psutil (see requirements.txt)

## Directory Locations

- Windows WSL: `/mnt/c/Users/zkysa/OneDrive/Zak/SmartNPCs/MCPThink/Streamlit-Interface-MCP-Host/`
- Linux/Mac: `~/ZAK-Agent/`

## Development Notes

- When modifying the chat functionality, the main logic is in `pages/BasicChat.py:process_command()`
- The application runs on port 8501 by default
- Streamlit configuration can be found in `~/.streamlit/config.toml` (if created)