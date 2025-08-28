import streamlit as st
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import MCPApiClient

# Page config
st.set_page_config(
    page_title="Session Monitor - MCP Host",
    page_icon="📊",
    layout="centered"
)

# Page header
st.title("📊 Session Monitor")
st.markdown("Raw JSON data from session endpoints")

# Refresh button
if st.button("🔄 Refresh", key="refresh"):
    st.rerun()

# Divider
st.divider()

try:
    # Initialize API client
    api_client = MCPApiClient()
    
    # Get health data (includes active sessions count)
    st.subheader("Health Status (with Active Sessions)")
    health_data = api_client.get_health()
    st.code(json.dumps(health_data, indent=2), language="json")
    
    # Optional: Get specific session status
    st.subheader("Session Status Lookup")
    session_id = st.text_input("Session ID (optional)", placeholder="Enter a session ID to view its status")
    
    if session_id:
        try:
            st.write(f"Status for session: `{session_id}`")
            session_data = api_client.get_session_status(session_id)
            st.code(json.dumps(session_data, indent=2), language="json")
        except Exception as e:
            st.error(f"Error fetching session {session_id}: {str(e)}")
    else:
        st.info("Enter a session ID above to view its status")
    
except Exception as e:
    st.error(f"Error fetching data: {str(e)}")
    st.info("Make sure the Agents-MCP-Host backend is running on port 8080.")