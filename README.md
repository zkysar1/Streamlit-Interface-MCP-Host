# Streamlit Interface for MCP Host

A modern web interface for the Agents-MCP-Host backend, providing chat interfaces and system monitoring through Server-Sent Events (SSE) streaming.

## Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   Streamlit Web UI  │────▶│   API Client Layer   │────▶│  Agents-MCP-Host    │
│      (Port 8501)    │     │  (utils/api_client)  │     │   Backend (8080)    │
│                     │     └──────────────────────┘     │                     │
│  ┌───────────────┐  │              │                    │  ┌───────────────┐  │
│  │ Chat Pages    │  │              ▼                    │  │ ConversationS │  │
│  ├───────────────┤  │     ┌──────────────────────┐     │  │ treaming API  │  │
│  │ • Database    │  │     │   SSE Event Stream   │     │  └───────────────┘  │
│  │ • SQL Builder │  │     │  ┌────────────────┐  │     │          │          │
│  │ • General     │  │     │  │ • connected    │  │     │          ▼          │
│  └───────────────┘  │◀────│  │ • progress     │  │◀────│  ┌───────────────┐  │
│                     │     │  │ • tool_*       │  │     │  │   Event Bus   │  │
│  ┌───────────────┐  │     │  │ • final        │  │     │  └───────────────┘  │
│  │ Monitor Pages │  │     │  │ • error        │  │     │          │          │
│  ├───────────────┤  │     │  └────────────────┘  │     │          ▼          │
│  │ • Dashboard   │  │     └──────────────────────┘     │  ┌───────────────┐  │
│  │ • Sessions    │  │                                  │  │ Host Services │  │
│  │ • MCP Tools   │  │     ┌──────────────────────┐     │  ├───────────────┤  │
│  └───────────────┘  │────▶│    REST Endpoints    │────▶│  │ • Oracle DB   │  │
│                     │     │   /host/v1/*        │     │  │ • SQL Builder │  │
└─────────────────────┘     └──────────────────────┘     │  │ • Direct LLM  │  │
                                                         │  └───────────────┘  │
                                                         └─────────────────────┘
```

## Components

### Chat Pages
- **Database Chat** - Natural language queries to Oracle database (oracledbanswerer)
- **SQL Builder Chat** - AI-assisted SQL query building (oraclesqlbuilder)
- **General Chat** - Direct LLM conversation without tools (toolfreedirectllm)

### Monitor Pages
- **System Dashboard** - Health status, system metrics, host availability
- **Session Monitor** - Active session tracking and management
- **MCP Tools** - View MCP system status and available tools

### Core Infrastructure
- **API Client** (`utils/api_client.py`) - Centralized backend communication
- **SSE Streaming** - Real-time event processing with progress tracking
- **Session State** - Isolated conversation history per chat page

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start backend (in Agents-MCP-Host directory)
java -jar build/libs/Agents-MCP-Host-1.0.0-fat.jar

# 3. Launch interface
streamlit run Home.py
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/host/v1/health` | GET | System health check |
| `/host/v1/status` | GET | Comprehensive status |
| `/host/v1/hosts/status` | GET | Host availability |
| `/host/v1/conversations` | POST | Main conversation API (SSE) |
| `/host/v1/conversations/{id}/interrupt` | POST | Interrupt active session |
| `/host/v1/conversations/{id}/status` | GET | Session status |
| `/host/v1/mcp/status` | GET | MCP system status |
| `/host/v1/mcp/tools` | GET | Available MCP tools |
| `/host/v1/mcp/clients` | GET | Connected MCP clients |

## Dependencies

- streamlit
- requests
- psutil

## License

MIT