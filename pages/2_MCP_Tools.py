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
    layout="wide"  # Changed to wide for better display
)

# Page header
st.title("🛠️ MCP Tools")
st.markdown("Model Context Protocol tools and clients overview")

# Refresh button
if st.button("🔄 Refresh", key="refresh"):
    st.rerun()

# Divider
st.divider()

# Initialize API client
api_client = MCPApiClient()

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["📊 System Overview", "🔧 Available Tools", "🖥️ Connected Clients"])

with tab1:
    st.subheader("MCP System Status")
    try:
        mcp_status = api_client.get_mcp_status()
        
        # Display key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "System Health",
                "✅ Healthy" if mcp_status.get("healthy", False) else "❌ Unhealthy",
                delta=None
            )
        
        with col2:
            st.metric(
                "Total MCP Clients",
                mcp_status.get("totalClients", 0),
                delta=f"{mcp_status.get('activeClients', 0)} active"
            )
            
        with col3:
            st.metric(
                "Available Tools",
                mcp_status.get("totalTools", 0),
                delta=None
            )
            
        with col4:
            st.metric(
                "Total Registrations",
                mcp_status.get("totalRegistrations", 0),
                delta=None
            )
        
        # Explain what the clients are
        with st.expander("ℹ️ Understanding MCP Clients"):
            st.info("""
            **What are the 11 MCP Clients?**
            
            The system uses multiple specialized MCP clients, each providing specific Oracle database capabilities:
            
            - **OracleQueryAnalysis** - Analyzes SQL queries
            - **OracleSchemaIntelligence** - Provides schema understanding
            - **BusinessMapping** - Maps business terms to database entities
            - **OracleSQLGeneration** - Generates SQL queries
            - **OracleSQLValidation** - Validates SQL syntax and logic
            - **OracleQueryExecution** - Executes queries against the database
            - **QueryIntentEvaluation** - Evaluates query intent
            - **StrategyGeneration** - Generates execution strategies
            - **IntentAnalysis** - Analyzes user intent
            - **StrategyOrchestrator** - Orchestrates multi-step strategies
            - **StrategyLearning** - Records and learns from executions
            
            Each client is a separate service that can be called independently, providing modular functionality.
            """)
        
        # Show warnings if any
        if "warnings" in mcp_status and mcp_status["warnings"]:
            st.warning("⚠️ System Warnings:")
            for warning in mcp_status["warnings"]:
                st.write(f"- {warning}")
                
    except Exception as e:
        st.error(f"Unable to fetch MCP status: {str(e)}")

with tab2:
    st.subheader("Available MCP Tools")
    try:
        mcp_tools = api_client.get_mcp_tools()
        
        if "tools" in mcp_tools and mcp_tools["tools"]:
            tools_list = mcp_tools["tools"]
            
            # Add search filter
            search_term = st.text_input("🔍 Search tools by name or description", "")
            
            # Filter tools based on search
            if search_term:
                filtered_tools = [
                    tool for tool in tools_list
                    if search_term.lower() in tool.get("name", "").lower() or
                       search_term.lower() in tool.get("description", "").lower()
                ]
            else:
                filtered_tools = tools_list
            
            st.write(f"Showing {len(filtered_tools)} of {len(tools_list)} tools")
            
            # Display each tool in an expandable card format
            for tool in filtered_tools:
                tool_name = tool.get("name", "Unknown")
                tool_desc = tool.get("description", "No description available")
                
                with st.expander(f"**{tool_name}** - {tool_desc[:100]}..." if len(tool_desc) > 100 else f"**{tool_name}** - {tool_desc}"):
                    
                    # Tool description
                    st.markdown("**Description:**")
                    st.write(tool_desc)
                    
                    # Input Schema
                    st.markdown("**Input Schema:**")
                    input_schema = tool.get("inputSchema", {})
                    
                    if input_schema:
                        # Check if it has properties (object type)
                        if "properties" in input_schema:
                            properties = input_schema.get("properties", {})
                            required_fields = input_schema.get("required", [])
                            
                            # Create a formatted display of the schema
                            schema_display = {
                                "type": input_schema.get("type", "object"),
                                "properties": {}
                            }
                            
                            for prop_name, prop_details in properties.items():
                                is_required = prop_name in required_fields
                                
                                # Ensure prop_details is a dictionary
                                if isinstance(prop_details, dict):
                                    prop_info = {
                                        "type": prop_details.get("type", "unknown"),
                                        "description": prop_details.get("description", ""),
                                        "required": is_required
                                    }
                                    
                                    # Add additional schema details if present
                                    if "format" in prop_details:
                                        prop_info["format"] = prop_details["format"]
                                    if "enum" in prop_details:
                                        prop_info["enum"] = prop_details["enum"]
                                    if "default" in prop_details:
                                        prop_info["default"] = prop_details["default"]
                                else:
                                    # Handle non-dict property (could be a simple type string)
                                    prop_info = {
                                        "type": str(prop_details) if prop_details else "unknown",
                                        "description": "",
                                        "required": is_required
                                    }
                                    
                                schema_display["properties"][prop_name] = prop_info
                            
                            # Add required fields list
                            if required_fields:
                                schema_display["required"] = required_fields
                            
                            # Display as formatted JSON
                            st.code(json.dumps(schema_display, indent=2), language="json")
                        else:
                            # Simple schema without properties
                            st.code(json.dumps(input_schema, indent=2), language="json")
                    else:
                        st.write("No input parameters required")
                    
                    # Available in clients
                    st.markdown("**Available in:**")
                    client_details = tool.get("clientDetails", [])
                    if client_details:
                        for client in client_details:
                            status = "🟢" if client.get("active", False) else "🔴"
                            st.write(f"{status} {client.get('serverName', 'Unknown')}")
                    
                    # Statistics if available
                    if "statistics" in tool and tool["statistics"]:
                        stats = tool["statistics"]
                        st.markdown("**Usage Statistics:**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Calls", stats.get("totalCalls", 0))
                        with col2:
                            st.metric("Success Rate", 
                                     f"{(stats.get('successfulCalls', 0) / max(stats.get('totalCalls', 1), 1) * 100):.1f}%")
                        with col3:
                            avg_duration = stats.get("averageDuration", 0)
                            st.metric("Avg Duration", f"{avg_duration:.0f}ms" if avg_duration else "N/A")
        else:
            st.info("No tools available. Make sure MCP clients are connected.")
            
    except Exception as e:
        st.error(f"Unable to fetch MCP tools: {str(e)}")

with tab3:
    st.subheader("Connected MCP Clients")
    try:
        mcp_clients = api_client.get_mcp_clients()
        
        if "clients" in mcp_clients and mcp_clients["clients"]:
            clients_list = mcp_clients["clients"]
            
            # Summary metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Clients", len(clients_list))
            with col2:
                active_count = sum(1 for c in clients_list if c.get("active", False))
                st.metric("Active Clients", active_count)
            
            # Display clients in a table format
            st.markdown("### Client Details")
            
            # Create table data
            table_data = []
            for client in clients_list:
                status = "✅ Active" if client.get("active", False) else "❌ Inactive"
                table_data.append({
                    "Status": status,
                    "Server Name": client.get("serverName", "Unknown"),
                    "Client ID": client.get("clientId", "")[:8] + "...",  # Truncate long IDs
                    "Tools": client.get("toolCount", 0),
                    "Uptime": f"{client.get('uptime', 0) / 1000 / 60:.0f} min"
                })
            
            # Display as a dataframe
            import pandas as pd
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Detailed view in expander
            with st.expander("View Detailed Client Information"):
                for client in clients_list:
                    st.markdown(f"#### {client.get('serverName', 'Unknown')}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Client ID:** `{client.get('clientId', 'N/A')}`")
                        st.write(f"**Server URL:** {client.get('serverUrl', 'N/A')}")
                        st.write(f"**Active:** {'Yes' if client.get('active', False) else 'No'}")
                    with col2:
                        st.write(f"**Tool Count:** {client.get('toolCount', 0)}")
                        st.write(f"**Event Bus:** {client.get('eventBusAddress', 'N/A')}")
                        uptime_ms = client.get('uptime', 0)
                        st.write(f"**Uptime:** {uptime_ms / 1000 / 60:.1f} minutes")
                    
                    # Show tools if available
                    if "toolNames" in client and client["toolNames"]:
                        st.write("**Available Tools:**")
                        tools_str = ", ".join(client["toolNames"])
                        st.write(tools_str)
                    
                    st.divider()
        else:
            st.info("No MCP clients connected. Make sure the MCP services are running.")
            
    except Exception as e:
        st.error(f"Unable to fetch MCP clients: {str(e)}")

# Footer with debug option
with st.expander("🐛 Debug: View Raw API Responses"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**MCP Status Response:**")
        try:
            status = api_client.get_mcp_status()
            st.code(json.dumps(status, indent=2), language="json")
        except Exception as e:
            st.error(f"Error: {e}")
    
    with col2:
        st.markdown("**MCP Tools Response:**")
        try:
            tools = api_client.get_mcp_tools()
            # Truncate for display if too large
            if "tools" in tools and len(tools["tools"]) > 2:
                display_tools = {
                    "tools": tools["tools"][:2],
                    "totalTools": tools.get("totalTools", 0),
                    "note": f"Showing 2 of {len(tools['tools'])} tools"
                }
                st.code(json.dumps(display_tools, indent=2), language="json")
            else:
                st.code(json.dumps(tools, indent=2), language="json")
        except Exception as e:
            st.error(f"Error: {e}")
    
    with col3:
        st.markdown("**MCP Clients Response:**")
        try:
            clients = api_client.get_mcp_clients()
            # Truncate for display if too large
            if "clients" in clients and len(clients["clients"]) > 2:
                display_clients = {
                    "clients": clients["clients"][:2],
                    "totalClients": clients.get("totalClients", 0),
                    "note": f"Showing 2 of {len(clients['clients'])} clients"
                }
                st.code(json.dumps(display_clients, indent=2), language="json")
            else:
                st.code(json.dumps(clients, indent=2), language="json")
        except Exception as e:
            st.error(f"Error: {e}")