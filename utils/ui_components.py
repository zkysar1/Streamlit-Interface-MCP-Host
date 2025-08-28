import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

def status_badge(status: str, text: Optional[str] = None) -> str:
    """Create a colored status badge"""
    colors = {
        "healthy": "🟢",
        "starting": "🟡",
        "degraded": "🟡", 
        "error": "🔴",
        "unavailable": "🔴",
        "available": "🟢",
        "true": "🟢",
        "false": "🔴",
        "running": "🟢",
        "stopped": "🔴",
        "unknown": "⚫",
        "ready": "🟢",
        "not ready": "🔴",
        "connected": "🟢",
        "disconnected": "🔴",
        "active": "🟢",
        "inactive": "🔴",
        "completed": "🟢"
    }
    
    status_lower = str(status).lower()
    emoji = colors.get(status_lower, "⚫")
    display_text = text or status
    
    return f"{emoji} {display_text}"

def refresh_button(key: str) -> bool:
    """Create a refresh button with timestamp"""
    col1, col2 = st.columns([1, 5])
    with col1:
        refresh = st.button("🔄 Refresh", key=f"refresh_{key}")
    with col2:
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    return refresh

def auto_refresh_settings(key: str) -> int:
    """Create auto-refresh settings widget"""
    col1, col2 = st.columns([2, 1])
    with col1:
        auto_refresh = st.checkbox("Auto-refresh", key=f"auto_refresh_{key}")
    with col2:
        if auto_refresh:
            interval = st.selectbox(
                "Interval",
                options=[5, 10, 30, 60],
                format_func=lambda x: f"{x}s",
                key=f"refresh_interval_{key}"
            )
        else:
            interval = 0
    return interval if auto_refresh else 0

def error_message(error: Exception) -> None:
    """Display formatted error message"""
    st.error(f"❌ {str(error)}")
    
    # Show retry suggestions based on error type
    if isinstance(error, ConnectionError):
        st.info("💡 Make sure the Agents-MCP-Host backend is running on port 8080")
    elif isinstance(error, TimeoutError):
        st.info("💡 The request took too long. The backend might be overloaded.")

def loading_spinner(text: str = "Loading...") -> Any:
    """Context manager for loading spinner"""
    return st.spinner(text)

def metric_card(title: str, value: Any, delta: Optional[Any] = None, 
                help_text: Optional[str] = None) -> None:
    """Create a metric card with optional delta and help text"""
    if help_text:
        st.metric(label=title, value=value, delta=delta, help=help_text)
    else:
        st.metric(label=title, value=value, delta=delta)

def expandable_json(title: str, data: Dict[str, Any], expanded: bool = False) -> None:
    """Display JSON data in an expandable section"""
    with st.expander(title, expanded=expanded):
        st.json(data)

def session_card(session: Dict[str, Any]) -> None:
    """Display a session information card"""
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            st.write(f"**Session ID:** `{session.get('sessionId', 'N/A')}`")
            st.caption(f"Conversation: {session.get('conversationId', 'N/A')}")
        
        with col2:
            duration = session.get('duration', 0)
            duration_str = format_duration(duration)
            st.write(f"**Duration:** {duration_str}")
            
        with col3:
            completed = session.get('completed', False)
            status = "Completed" if completed else "Active"
            st.write(status_badge(status.lower(), status))
            
        with col4:
            # Action buttons will be added by the caller
            st.write("")  # Placeholder

def format_duration(milliseconds: int) -> str:
    """Format duration from milliseconds to readable string"""
    seconds = milliseconds // 1000
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hours}h {mins}m"

def host_status_card(host: Dict[str, Any]) -> None:
    """Display host status in a card format"""
    available = host.get('available', False)
    name = host.get('name', 'Unknown')
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(name)
            
        with col2:
            st.write(status_badge("available" if available else "unavailable"))
        
        # Additional host details if available
        if 'activeConnections' in host:
            st.caption(f"Active connections: {host['activeConnections']}")
        if 'lastSeen' in host:
            st.caption(f"Last seen: {format_timestamp(host['lastSeen'])}")

def format_timestamp(timestamp: int) -> str:
    """Format timestamp to readable string"""
    try:
        return datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Invalid timestamp"

def progress_bar_with_text(progress: float, text: str) -> None:
    """Display a progress bar with text"""
    progress_container = st.container()
    with progress_container:
        st.progress(progress)
        st.caption(text)

def collapsible_logs(logs: List[str], title: str = "Logs", max_height: int = 300) -> None:
    """Display logs in a collapsible, scrollable container"""
    with st.expander(title):
        log_text = "\n".join(logs)
        st.text_area("", value=log_text, height=max_height, disabled=True)

def critical_error_alert(errors: List[Dict[str, Any]]) -> None:
    """Display critical error alerts"""
    if errors:
        st.error(f"⚠️ {len(errors)} critical error(s) detected!")
        
        for i, error in enumerate(errors[:5]):  # Show max 5 errors
            with st.expander(f"Error {i+1}: {error.get('message', 'Unknown error')}", expanded=i==0):
                st.write(f"**Time:** {format_timestamp(error.get('timestamp', 0))}")
                st.write(f"**Severity:** {error.get('severity', 'UNKNOWN')}")
                if 'details' in error:
                    st.json(error['details'])

def connection_status_indicator(is_connected: bool, text: str = "Connection Status") -> None:
    """Show connection status with animated indicator"""
    if is_connected:
        st.success(f"{text}: Connected 🟢")
    else:
        st.error(f"{text}: Disconnected 🔴")

def create_sidebar_filters() -> Dict[str, Any]:
    """Create common sidebar filters"""
    st.sidebar.header("Filters")
    
    filters = {}
    
    # Time range filter
    time_range = st.sidebar.selectbox(
        "Time Range",
        ["Last 5 min", "Last 15 min", "Last hour", "Last 24 hours", "All time"],
        key="time_range_filter"
    )
    filters['time_range'] = time_range
    
    # Status filter
    status_filter = st.sidebar.multiselect(
        "Status",
        ["Active", "Completed", "Failed", "Timeout"],
        default=["Active"],
        key="status_filter"
    )
    filters['status'] = status_filter
    
    return filters

def display_api_response_time(response_time_ms: int) -> None:
    """Display API response time with color coding"""
    if response_time_ms < 100:
        color = "green"
    elif response_time_ms < 500:
        color = "orange"  
    else:
        color = "red"
        
    st.markdown(f"Response time: <span style='color:{color}'>{response_time_ms}ms</span>", 
                unsafe_allow_html=True)

def create_dataframe_with_actions(df, actions: List[Dict[str, Any]]) -> None:
    """
    Create a dataframe with action buttons for each row
    actions: List of dicts with 'label', 'callback', and optional 'confirm' keys
    """
    # Display the dataframe
    st.dataframe(df, use_container_width=True)
    
    # Add action buttons for each row
    for idx, row in df.iterrows():
        cols = st.columns([1] * len(actions) + [3])
        for i, action in enumerate(actions):
            with cols[i]:
                if st.button(action['label'], key=f"{action['label']}_{idx}"):
                    if action.get('confirm', False):
                        if st.checkbox(f"Confirm {action['label']}", key=f"confirm_{action['label']}_{idx}"):
                            action['callback'](row)
                    else:
                        action['callback'](row)