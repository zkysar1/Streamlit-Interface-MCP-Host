import streamlit as st
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import MCPApiClient

# Page config
st.set_page_config(
    page_title="MCP Tools - MCP Host",
    page_icon="🛠️",
    layout="centered"
)

# Page header
st.title("🛠️ MCP Tools")
st.markdown("Raw JSON data from MCP endpoints")

# Refresh button
if st.button("🔄 Refresh", key="refresh"):
    st.rerun()

# Divider
st.divider()

# Initialize API client
api_client = MCPApiClient()

# Get MCP status
st.subheader("MCP System Status")
try:
    mcp_status = api_client.get_mcp_status()
except Exception as e:
    mcp_status = {
        "error": "MCP status endpoint error",
        "message": str(e),
        "endpoint": "/host/v1/mcp/status",
        "note": "The MCP event bus handler may not be registered"
    }
st.code(json.dumps(mcp_status, indent=2), language="json")

# Get available tools
st.subheader("Available MCP Tools")
try:
    mcp_tools = api_client.get_mcp_tools()
except Exception as e:
    mcp_tools = {
        "error": "MCP tools endpoint error",
        "message": str(e),
        "endpoint": "/host/v1/mcp/tools",
        "note": "The MCP event bus handler may not be registered"
    }
st.code(json.dumps(mcp_tools, indent=2), language="json")

# Get connected clients
st.subheader("Connected MCP Clients")
try:
    mcp_clients = api_client.get_mcp_clients()
except Exception as e:
    mcp_clients = {
        "error": "MCP clients endpoint error",
        "message": str(e),
        "endpoint": "/host/v1/mcp/clients",
        "note": "The MCP event bus handler may not be registered"
    }
st.code(json.dumps(mcp_clients, indent=2), language="json")

# Info message at the bottom
st.divider()
st.info("Note: If you see error messages above, the MCP event bus handlers may not be registered in the backend. The endpoints exist but require corresponding event bus consumers.")