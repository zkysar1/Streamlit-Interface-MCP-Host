import streamlit as st
import time
from datetime import datetime
import sys
import os
import copy

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import MCPApiClient
from utils.ui_components import (
    status_badge, refresh_button, auto_refresh_settings, 
    error_message, loading_spinner, metric_card,
    expandable_json, critical_error_alert, format_duration
)

# Page config
st.set_page_config(
    page_title="System Dashboard - MCP Host",
    page_icon="🏠",
    layout="wide"
)

# Initialize API client
@st.cache_resource
def get_api_client():
    return MCPApiClient()

api_client = get_api_client()

# Page header
st.title("🏠 System Dashboard")
st.markdown("Real-time monitoring of the Agents-MCP-Host system")

# Auto-refresh settings
refresh_interval = auto_refresh_settings("dashboard")

# Manual refresh button
manual_refresh = refresh_button("dashboard")

# Initialize session state
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

if 'dashboard_data' not in st.session_state:
    st.session_state.dashboard_data = {
        'health': None,
        'status': None,
        'hosts': None,
        'errors': []
    }

if 'error_count' not in st.session_state:
    st.session_state.error_count = 0

if 'last_error_time' not in st.session_state:
    st.session_state.last_error_time = 0

# Function to fetch all data
def fetch_dashboard_data():
    """Fetch all dashboard data from API endpoints"""
    errors = []
    data = {}
    
    # Fetch health
    try:
        with loading_spinner("Fetching health status..."):
            data['health'] = api_client.get_health()
    except Exception as e:
        errors.append(("Health", e))
        data['health'] = None
    
    # Fetch status
    try:
        with loading_spinner("Fetching system status..."):
            data['status'] = api_client.get_status()
    except Exception as e:
        errors.append(("Status", e))
        data['status'] = None
    
    # Fetch hosts
    try:
        with loading_spinner("Fetching host status..."):
            data['hosts'] = api_client.get_hosts_status()
    except Exception as e:
        errors.append(("Hosts", e))
        data['hosts'] = None
    
    return data, errors

# Check if refresh needed
should_refresh = manual_refresh or (
    refresh_interval > 0 and 
    time.time() - st.session_state.last_refresh >= refresh_interval
)

# Reset error count on manual refresh
if manual_refresh:
    st.session_state.error_count = 0

if should_refresh or st.session_state.dashboard_data['health'] is None:
    data, errors = fetch_dashboard_data()
    st.session_state.dashboard_data = data
    st.session_state.dashboard_data['errors'] = errors
    st.session_state.last_refresh = time.time()
    
    # Error handling for auto-refresh
    if errors:
        st.session_state.error_count += 1
        st.session_state.last_error_time = time.time()
        
        # Stop auto-refresh if too many consecutive errors
        if st.session_state.error_count >= 3:
            st.warning(f"Auto-refresh paused due to {st.session_state.error_count} consecutive errors. Please check your connection and refresh manually.")
            refresh_interval = 0  # Disable auto-refresh
    else:
        # Reset error count on successful fetch
        st.session_state.error_count = 0
    
    if refresh_interval > 0 and st.session_state.error_count < 3:
        time.sleep(0.1)  # Small delay to prevent UI flicker
        st.rerun()

# Display errors if any
if st.session_state.dashboard_data['errors']:
    for endpoint, error in st.session_state.dashboard_data['errors']:
        st.error(f"Failed to fetch {endpoint} data")
        error_message(error)

# Main dashboard layout
health_data = st.session_state.dashboard_data.get('health', {})
status_data = st.session_state.dashboard_data.get('status', {})
hosts_data = st.session_state.dashboard_data.get('hosts', {})

# Row 1: Key Metrics
st.markdown("### 📊 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    system_ready = health_data.get('systemReady', False) if health_data else False
    health_status = health_data.get('status', 'unknown') if health_data else 'unknown'
    metric_card(
        "System Status",
        status_badge(health_status, health_status.capitalize()),
        help_text="Overall system health status"
    )

with col2:
    active_sessions = health_data.get('activeSessions', 0) if health_data else 0
    metric_card(
        "Active Sessions",
        active_sessions,
        help_text="Number of active streaming sessions"
    )

with col3:
    uptime_ms = status_data.get('uptime', 0) if status_data else 0
    uptime_str = api_client.calculate_uptime(uptime_ms) if uptime_ms else "N/A"
    metric_card(
        "Uptime",
        uptime_str,
        help_text="Time since service started"
    )

with col4:
    critical_errors = health_data.get('criticalErrors', 0) if health_data else 0
    metric_card(
        "Critical Errors",
        critical_errors,
        delta=critical_errors if critical_errors > 0 else None,
        help_text="Number of unresolved critical errors"
    )

# Row 2: System Readiness and Database
st.markdown("### 🔧 System Components")
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### System Readiness")
    if health_data:
        ready_status = "Ready" if health_data.get('systemReady', False) else "Not Ready"
        st.info(f"{status_badge(ready_status.lower(), ready_status)}")
        
        if not health_data.get('systemReady', False):
            st.warning("System is still initializing. Some features may not be available.")
    else:
        st.warning("Health data not available")

with col2:
    st.markdown("#### Database Status")
    if status_data and 'database' in status_data:
        db_data = status_data['database']
        db_healthy = db_data.get('healthy', False)
        db_status = "Connected" if db_healthy else "Disconnected"
        
        st.info(f"{status_badge(db_status.lower(), db_status)}")
        
        if db_healthy:
            st.caption(f"Active: {db_data.get('activeConnections', 0)} | "
                      f"Idle: {db_data.get('idleConnections', 0)} | "
                      f"Total: {db_data.get('totalConnections', 0)}")
        else:
            if 'error' in db_data:
                st.error(f"Error: {db_data['error']}")
    else:
        st.warning("Database status not available")

# Row 3: Host Status
st.markdown("### 🖥️ Host Status")
if hosts_data and 'hosts' in hosts_data:
    hosts = hosts_data['hosts']
    host_cols = st.columns(len(hosts))
    
    for i, host in enumerate(hosts):
        with host_cols[i]:
            host_name = host.get('name', 'Unknown')
            host_available = host.get('available', False)
            
            st.markdown(f"**{host_name}**")
            st.write(status_badge("available" if host_available else "unavailable"))
            
            # Additional host metrics if available
            if 'activeRequests' in host:
                st.caption(f"Active: {host['activeRequests']}")
            if 'avgResponseTime' in host:
                st.caption(f"Avg Response: {host['avgResponseTime']}ms")
else:
    st.info("Host information not available")

# Row 4: MCP Status Summary
st.markdown("### 🔌 MCP Status")
if status_data and 'mcp' in status_data:
    mcp_data = status_data['mcp']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'error' not in mcp_data:
            clients = mcp_data.get('clients', {})
            active_clients = len([c for c in clients.values() if c.get('status') == 'active'])
            total_clients = len(clients)
            st.metric("MCP Clients", f"{active_clients}/{total_clients}")
        else:
            st.metric("MCP Clients", "Error")
            st.caption(mcp_data.get('message', 'Unknown error'))
    
    with col2:
        if 'error' not in mcp_data:
            tools_count = len(mcp_data.get('tools', []))
            st.metric("Available Tools", tools_count)
        else:
            st.metric("Available Tools", "N/A")
    
    with col3:
        if 'error' not in mcp_data:
            mcp_status = "Active" if mcp_data.get('isActive', False) else "Inactive"
            st.write(status_badge(mcp_status.lower(), f"MCP {mcp_status}"))
        else:
            st.write(status_badge("error", "MCP Error"))
else:
    st.info("MCP status will be displayed here when available")

# Row 5: Critical Errors (if any)
if critical_errors > 0:
    st.markdown("### ⚠️ Critical Errors")
    st.error(f"{critical_errors} critical error(s) detected in the system!")
    
    # In a real implementation, we would fetch error details
    # For now, just show the count
    st.warning("Check the logs for more details about critical errors.")

# Expandable sections for raw data
st.markdown("### 📋 Raw Data")
col1, col2, col3 = st.columns(3)

with col1:
    if health_data:
        expandable_json("Health Data", health_data)

with col2:
    if status_data:
        # Remove sensitive data before displaying (use deepcopy to avoid modifying original)
        safe_status = copy.deepcopy(status_data)
        if 'database' in safe_status and 'connectionString' in safe_status['database']:
            safe_status['database']['connectionString'] = "***hidden***"
        expandable_json("Status Data", safe_status)

with col3:
    if hosts_data:
        expandable_json("Hosts Data", hosts_data)

# Environment info at the bottom
with st.expander("Environment Information"):
    if status_data:
        st.write(f"**Version:** {status_data.get('version', 'Unknown')}")
        st.write(f"**Environment:** {status_data.get('environment', 'Unknown')}")
        st.write(f"**Server Start Time:** {api_client.format_timestamp(status_data.get('timestamp', 0) - status_data.get('uptime', 0))}")
        st.write(f"**Current Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")