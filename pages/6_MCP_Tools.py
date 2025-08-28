import streamlit as st
import time
from datetime import datetime
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import MCPApiClient
from utils.ui_components import (
    status_badge, refresh_button, auto_refresh_settings,
    error_message, loading_spinner, metric_card,
    expandable_json, connection_status_indicator
)

# Page config
st.set_page_config(
    page_title="MCP Tools Explorer - MCP Host",
    page_icon="🛠️",
    layout="wide"
)

# Initialize API client
@st.cache_resource
def get_api_client():
    return MCPApiClient()

api_client = get_api_client()

# Page header
st.title("🛠️ MCP Tools Explorer")
st.markdown("Explore available Model Context Protocol tools and clients")

# Initialize session state
if 'mcp_data' not in st.session_state:
    st.session_state.mcp_data = {
        'status': None,
        'tools': None,
        'clients': None
    }

if 'last_mcp_refresh' not in st.session_state:
    st.session_state.last_mcp_refresh = 0

if 'selected_tool' not in st.session_state:
    st.session_state.selected_tool = None

# Auto-refresh settings
refresh_interval = auto_refresh_settings("mcp")

# Manual refresh button
manual_refresh = refresh_button("mcp")

# Function to fetch MCP data
def fetch_mcp_data():
    """Fetch all MCP-related data"""
    data = {}
    errors = []
    
    # Fetch MCP status
    try:
        with loading_spinner("Fetching MCP status..."):
            data['status'] = api_client.get_mcp_status()
    except Exception as e:
        errors.append(("MCP Status", e))
        data['status'] = None
    
    # Fetch tools
    try:
        with loading_spinner("Fetching available tools..."):
            data['tools'] = api_client.get_mcp_tools()
    except Exception as e:
        errors.append(("Tools", e))
        data['tools'] = None
    
    # Fetch clients
    try:
        with loading_spinner("Fetching MCP clients..."):
            data['clients'] = api_client.get_mcp_clients()
    except Exception as e:
        errors.append(("Clients", e))
        data['clients'] = None
    
    return data, errors

# Check if refresh needed
should_refresh = manual_refresh or (
    refresh_interval > 0 and 
    time.time() - st.session_state.last_mcp_refresh >= refresh_interval
)

if should_refresh or st.session_state.mcp_data['status'] is None:
    data, errors = fetch_mcp_data()
    st.session_state.mcp_data = data
    st.session_state.last_mcp_refresh = time.time()
    
    # Display errors if any
    for endpoint, error in errors:
        st.error(f"Failed to fetch {endpoint}")
        error_message(error)
    
    if refresh_interval > 0:
        time.sleep(0.1)
        st.rerun()

# Display MCP Status
st.markdown("### 📊 MCP System Status")

mcp_status = st.session_state.mcp_data.get('status', {})
if mcp_status and 'error' not in mcp_status:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        is_active = mcp_status.get('isActive', False)
        status_text = "Active" if is_active else "Inactive"
        metric_card("MCP Status", status_badge(status_text.lower(), status_text))
    
    with col2:
        client_count = len(mcp_status.get('clients', {}))
        metric_card("Connected Clients", client_count)
    
    with col3:
        tool_count = len(mcp_status.get('tools', []))
        metric_card("Available Tools", tool_count)
    
    with col4:
        server_count = len(mcp_status.get('servers', {}))
        metric_card("MCP Servers", server_count)
else:
    st.warning("MCP status information not available")

# Display Tools
st.markdown("---")
st.markdown("### 🔧 Available Tools")

tools_data = st.session_state.mcp_data.get('tools', {})
if tools_data and 'error' not in tools_data:
    tools = tools_data.get('tools', [])
    
    if tools:
        # Tool search/filter
        search_term = st.text_input("🔍 Search tools", placeholder="Enter tool name or description...")
        
        # Filter tools based on search
        filtered_tools = [
            tool for tool in tools 
            if search_term.lower() in tool.get('name', '').lower() or 
               search_term.lower() in tool.get('description', '').lower()
        ] if search_term else tools
        
        # Display tools in a grid
        st.info(f"Showing {len(filtered_tools)} of {len(tools)} tools")
        
        # Create columns for tool cards
        cols_per_row = 3
        for i in range(0, len(filtered_tools), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j in range(cols_per_row):
                if i + j < len(filtered_tools):
                    tool = filtered_tools[i + j]
                    
                    with cols[j]:
                        with st.container():
                            st.markdown(f"#### {tool.get('name', 'Unknown')}")
                            st.caption(tool.get('description', 'No description available'))
                            
                            # Tool metadata
                            if 'inputSchema' in tool:
                                st.write("**Input Schema:**")
                                st.code(json.dumps(tool['inputSchema'], indent=2), language='json')
                            
                            if st.button(f"View Details", key=f"tool_{tool.get('name', '')}_{i}_{j}"):
                                st.session_state.selected_tool = tool
    else:
        st.info("No tools are currently available")
else:
    st.warning("Unable to fetch tools information")

# Display selected tool details
if st.session_state.selected_tool:
    st.markdown("---")
    st.markdown(f"### 📋 Tool Details: {st.session_state.selected_tool.get('name', 'Unknown')}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        expandable_json("Full Tool Specification", st.session_state.selected_tool, expanded=True)
    
    with col2:
        st.button("Close Details", on_click=lambda: setattr(st.session_state, 'selected_tool', None))

# Display Clients
st.markdown("---")
st.markdown("### 👥 Connected MCP Clients")

clients_data = st.session_state.mcp_data.get('clients', {})
if clients_data and 'error' not in clients_data:
    clients = clients_data.get('clients', {})
    
    if clients:
        client_cols = st.columns(len(clients))
        
        for idx, (client_id, client_info) in enumerate(clients.items()):
            with client_cols[idx]:
                st.markdown(f"#### Client {idx + 1}")
                st.code(client_id[:12] + "..." if len(client_id) > 12 else client_id)
                
                status = client_info.get('status', 'unknown')
                st.write(status_badge(status, status.capitalize()))
                
                if 'connectedAt' in client_info:
                    connected_time = api_client.format_timestamp(client_info['connectedAt'])
                    st.caption(f"Connected: {connected_time}")
                
                if 'lastSeen' in client_info:
                    last_seen = api_client.format_timestamp(client_info['lastSeen'])
                    st.caption(f"Last seen: {last_seen}")
    else:
        st.info("No MCP clients are currently connected")
else:
    st.warning("Unable to fetch client information")

# MCP Configuration Info
st.markdown("---")
st.markdown("### ⚙️ MCP Configuration")

with st.expander("MCP System Information"):
    if mcp_status and 'error' not in mcp_status:
        st.json(mcp_status)
    else:
        st.warning("MCP configuration details not available")

# Documentation
st.markdown("---")
st.markdown("### 📚 MCP Documentation")

with st.expander("About Model Context Protocol"):
    st.markdown("""
    The **Model Context Protocol (MCP)** is a standardized interface for connecting AI models 
    to external tools and data sources. It enables:
    
    - **Tool Discovery**: Automatically discover available tools and their capabilities
    - **Schema Validation**: Ensure proper input/output formats for tool calls
    - **Client Management**: Track and manage connected clients
    - **Server Federation**: Connect multiple MCP servers for expanded capabilities
    
    #### Key Components:
    
    1. **MCP Servers**: Provide tools and resources
    2. **MCP Clients**: Consume tools and make requests
    3. **Tools**: Individual functions with defined schemas
    4. **Resources**: Data sources accessible through MCP
    
    #### Benefits:
    
    - 🔌 **Pluggable Architecture**: Easy to add new tools
    - 🛡️ **Type Safety**: Schema validation prevents errors
    - 🚀 **Scalability**: Distributed tool hosting
    - 📊 **Observability**: Track tool usage and performance
    """)

# Tips
with st.expander("💡 Tips for Using MCP Tools"):
    st.markdown("""
    - **Tool Selection**: The system automatically selects appropriate tools based on the query
    - **Schema Compliance**: All tool inputs are validated against their schemas
    - **Error Handling**: Tools provide structured error responses
    - **Performance**: Tool execution times vary based on complexity
    - **Availability**: Tools may be temporarily unavailable during updates
    """)

# Auto-refresh logic
if refresh_interval > 0:
    time.sleep(refresh_interval)
    st.rerun()