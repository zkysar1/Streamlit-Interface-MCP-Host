import streamlit as st
import time
from datetime import datetime
import pandas as pd
import sys
import os
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import MCPApiClient
from utils.ui_components import (
    status_badge, refresh_button, auto_refresh_settings,
    error_message, loading_spinner, session_card,
    expandable_json, format_duration, collapsible_logs
)

# Page config
st.set_page_config(
    page_title="Session Monitor - MCP Host",
    page_icon="📊",
    layout="wide"
)

# Initialize API client
@st.cache_resource
def get_api_client():
    return MCPApiClient()

api_client = get_api_client()

# Page header
st.title("📊 Session Monitor")
st.markdown("Monitor and manage active streaming sessions")

# Initialize session state
if 'active_sessions' not in st.session_state:
    st.session_state.active_sessions = []

if 'session_history' not in st.session_state:
    st.session_state.session_history = []

if 'selected_session' not in st.session_state:
    st.session_state.selected_session = None

# Sidebar controls
st.sidebar.header("Session Controls")

# Auto-refresh settings in sidebar
auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
if auto_refresh:
    refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 5, 60, 10)
else:
    refresh_interval = 0

# Manual refresh button
if st.sidebar.button("🔄 Refresh Now"):
    st.session_state.force_refresh = True

# Get active sessions from health endpoint
def get_active_sessions():
    """Fetch active sessions count and details"""
    try:
        health_data = api_client.get_health()
        active_count = health_data.get('activeSessions', 0)
        return active_count
    except Exception as e:
        st.error("Failed to fetch session data")
        error_message(e)
        return 0

# Main content area
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    st.markdown("### Active Sessions")
    active_count = get_active_sessions()
    st.metric("Currently Active", active_count)

with col2:
    st.markdown("### Session History")
    st.metric("Total Today", len(st.session_state.session_history))

# Session management functions
def interrupt_session(session_id: str):
    """Interrupt an active session"""
    try:
        with loading_spinner(f"Interrupting session {session_id}..."):
            result = api_client.interrupt_session(session_id)
            st.success(f"Session {session_id} interrupted successfully")
            return True
    except Exception as e:
        st.error(f"Failed to interrupt session {session_id}")
        error_message(e)
        return False

def cancel_session(session_id: str):
    """Cancel/delete a session"""
    try:
        with loading_spinner(f"Cancelling session {session_id}..."):
            result = api_client.cancel_session(session_id)
            st.success(f"Session {session_id} cancelled successfully")
            return True
    except Exception as e:
        st.error(f"Failed to cancel session {session_id}")
        error_message(e)
        return False

def submit_feedback(session_id: str, feedback_data: dict):
    """Submit feedback for a session"""
    try:
        with loading_spinner("Submitting feedback..."):
            result = api_client.submit_feedback(session_id, feedback_data)
            st.success("Feedback submitted successfully")
            return True
    except Exception as e:
        st.error("Failed to submit feedback")
        error_message(e)
        return False

def get_session_details(session_id: str):
    """Get detailed status of a specific session"""
    try:
        return api_client.get_session_status(session_id)
    except:
        return None

# Session input for testing
st.markdown("---")
st.markdown("### Test Session Operations")
st.info("Since we can't list all sessions from the current API, you can enter a session ID to test operations")

col1, col2 = st.columns([3, 1])
with col1:
    test_session_id = st.text_input("Session ID", placeholder="Enter a session ID from your chat")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    check_status = st.button("Check Status")

if test_session_id and check_status:
    # Validate session ID format (basic UUID validation)
    # Proper UUID format: 8-4-4-4-12 hex digits with hyphens
    if not re.match(r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$', test_session_id):
        st.error("Invalid session ID format. Please enter a valid session ID.")
    else:
        session_details = get_session_details(test_session_id)
        if session_details:
            st.success("Session found!")
            
            # Display session details
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Session ID", test_session_id[:8] + "...")
                
            with col2:
                duration_ms = session_details.get('duration', 0)
                st.metric("Duration", format_duration(duration_ms))
                
            with col3:
                completed = session_details.get('completed', False)
                status = "Completed" if completed else "Active"
                st.write(status_badge(status.lower(), status))
                
            with col4:
                host = session_details.get('host', 'Unknown')
                st.metric("Host", host)
            
            # Action buttons
            st.markdown("#### Actions")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if not completed and st.button("⏸️ Interrupt", key=f"interrupt_{test_session_id}"):
                    if interrupt_session(test_session_id):
                        time.sleep(1)
                        st.rerun()
            
            with col2:
                if st.button("❌ Cancel", key=f"cancel_{test_session_id}"):
                    if cancel_session(test_session_id):
                        time.sleep(1)
                        st.rerun()
            
            with col3:
                if st.button("💬 Feedback", key=f"feedback_{test_session_id}"):
                    st.session_state.selected_session = test_session_id
            
            # Show raw session data
            expandable_json("Session Details", session_details)
            
        else:
            st.error("Session not found or already completed")

# Feedback form
if st.session_state.selected_session:
    st.markdown("---")
    st.markdown(f"### Submit Feedback for Session {st.session_state.selected_session[:8]}...")
    
    with st.form("feedback_form"):
        rating = st.slider("Rating", 1, 5, 3)
        feedback_text = st.text_area("Comments", placeholder="Enter your feedback here...")
        helpful = st.checkbox("Was this response helpful?")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Submit Feedback")
        with col2:
            cancel = st.form_submit_button("Cancel")
        
        if submit:
            feedback_data = {
                "rating": rating,
                "comment": feedback_text,
                "helpful": helpful,
                "timestamp": int(time.time() * 1000)
            }
            if submit_feedback(st.session_state.selected_session, feedback_data):
                st.session_state.selected_session = None
                st.rerun()
        
        if cancel:
            st.session_state.selected_session = None
            st.rerun()

# Session Analytics (placeholder)
st.markdown("---")
st.markdown("### Session Analytics")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Session Duration Distribution")
    st.info("📊 Analytics will be displayed here when session history is available")
    
    # Placeholder chart
    import random
    durations = [random.randint(5, 300) for _ in range(10)]
    df = pd.DataFrame({
        'Session': [f"Session {i}" for i in range(10)],
        'Duration (seconds)': durations
    })
    st.bar_chart(df.set_index('Session'))

with col2:
    st.markdown("#### Sessions by Host")
    st.info("📊 Host distribution will be displayed here")
    
    # Placeholder pie chart data
    host_data = {
        'oracledbanswerer': 45,
        'oraclesqlbuilder': 30,
        'toolfreedirectllm': 25
    }
    st.write("Distribution:")
    for host, percentage in host_data.items():
        st.write(f"- {host}: {percentage}%")

# Tips section
with st.expander("💡 Tips for Session Management"):
    st.markdown("""
    - **Active Sessions**: Shows currently running streaming sessions
    - **Interrupt**: Gracefully stops a session, allowing cleanup
    - **Cancel**: Forcefully terminates a session
    - **Feedback**: Submit user feedback for completed sessions
    
    **Session States:**
    - 🟢 Active: Session is currently processing
    - 🟡 Interrupted: Session was gracefully stopped
    - 🔴 Cancelled: Session was forcefully terminated
    - ✅ Completed: Session finished successfully
    """)

# Auto-refresh logic
if auto_refresh and refresh_interval > 0:
    time.sleep(refresh_interval)
    st.rerun()