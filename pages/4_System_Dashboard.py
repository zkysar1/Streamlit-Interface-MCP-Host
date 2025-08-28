import streamlit as st
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import MCPApiClient

# Page config
st.set_page_config(
    page_title="System Dashboard - MCP Host",
    page_icon="🏠",
    layout="centered"
)

# Page header
st.title("🏠 System Dashboard")
st.markdown("Raw JSON data from system endpoints")

# Refresh button
if st.button("🔄 Refresh", key="refresh"):
    st.rerun()

# Divider
st.divider()

try:
    # Initialize API client
    api_client = MCPApiClient()
    
    # Get health data
    st.subheader("Health Status")
    health_data = api_client.get_health()
    st.code(json.dumps(health_data, indent=2), language="json")
    
    # Get comprehensive status
    st.subheader("Comprehensive Status")
    status_data = api_client.get_status()
    st.code(json.dumps(status_data, indent=2), language="json")
    
    # Get hosts status
    st.subheader("Hosts Status")
    hosts_data = api_client.get_hosts_status()
    st.code(json.dumps(hosts_data, indent=2), language="json")
    
except Exception as e:
    st.error(f"Error fetching data: {str(e)}")
    st.info("Make sure the Agents-MCP-Host backend is running on port 8080.")