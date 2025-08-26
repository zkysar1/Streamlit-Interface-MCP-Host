import psutil
import os
import requests
import json
import streamlit as st
import time
from datetime import datetime
import uuid
from typing import Dict, List, Optional, Tuple


st.title("Client Holding Challenge Agent")
st.write("""
### Basic Chat for supporing one challenge at a time? 
Zak Kysar *DRAFT*
""")


class StreamingSession:
    """Stores streaming state that persists across Streamlit reruns"""
    
    def __init__(self, message_id: str):
        self.message_id = message_id
        self.events: List[Dict] = []
        self.is_active = True
        self.final_response: Optional[str] = None
        self.error: Optional[str] = None
        self.start_time = time.time()
        self.stream_id: Optional[str] = None
        self.completed_tools: List[str] = []
        self.current_phase = "Starting"
        self.current_tool = None
        self.step_info = {}
        
    def is_stale(self, timeout_seconds: int = 600) -> bool:
        """Check if stream has been active too long without completion"""
        if self.is_active and (time.time() - self.start_time) > timeout_seconds:
            return True
        return False
        
    def add_event(self, event_type: str, data):
        """Add an event to the session history"""
        self.events.append({
            'type': event_type,
            'data': data,
            'timestamp': time.time() - self.start_time
        })
        
        # Update session state based on event
        if event_type == 'connected':
            if isinstance(data, str):
                self.stream_id = data
            elif isinstance(data, dict) and data is not None:
                self.stream_id = data.get('streamId')
        elif event_type == 'tool_call_complete':
            if isinstance(data, dict) and data is not None:
                tool_name = data.get('tool', '').replace('oracle__', '').replace('_', ' ').title()
                if tool_name and tool_name not in self.completed_tools:
                    self.completed_tools.append(tool_name)
        elif event_type == 'final_response':
            if isinstance(data, str):
                self.final_response = data
            elif isinstance(data, dict) and data is not None:
                self.final_response = data.get('content', '')
            self.is_active = False
        elif event_type == 'error':
            if isinstance(data, dict) and data is not None:
                self.error = data.get('message', 'Unknown error')
            self.is_active = False
            
    def get_display_events(self, verbosity: str) -> List[Dict]:
        """Filter events based on verbosity level"""
        if verbosity == 'Minimal':
            # Only show final response and errors
            return [e for e in self.events if e['type'] in ['final_response', 'error']]
        elif verbosity == 'Normal':
            # Show important events
            important_types = {
                'tool_call_start', 'tool_call_complete', 
                'execution_paused', 'agent_question', 
                'error', 'final_response'
            }
            return [e for e in self.events if e['type'] in important_types]
        else:  # Detailed
            # Show all events
            return self.events


class ProgressManager:
    """Manages progress display with minimal verbosity and smart updates"""
    
    def __init__(self, container, session: Optional[StreamingSession] = None):
        self.container = container
        self.progress_placeholder = container.empty()
        self.session = session
        
        # Initialize from session if available
        if session:
            self.start_time = session.start_time
            self.current_phase = session.current_phase
            self.current_tool = session.current_tool
            self.completed_tools = session.completed_tools.copy()
            self.step_info = session.step_info.copy()
        else:
            self.start_time = time.time()
            self.current_phase = "Starting"
            self.current_tool = None
            self.completed_tools = []
            self.step_info = {}
            
        self.is_long_running = False
        self.error_occurred = False
        
        # Event types to show in main view
        self.important_events = {
            'tool_call_start', 'tool_call_complete', 
            'execution_paused', 'agent_question', 'error'
        }
        
    def update_progress(self, phase=None, tool=None):
        """Update the progress display in place"""
        elapsed = time.time() - self.start_time
        
        if phase:
            self.current_phase = phase
            if self.session:
                self.session.current_phase = phase
        if tool:
            self.current_tool = tool
            if self.session:
                self.session.current_tool = tool
                
        with self.progress_placeholder.container():
            # Check if operation is taking long
            if elapsed > 30 and not self.is_long_running:
                self.is_long_running = True
                st.info(f"""
                ⏳ **Still working...** ({elapsed:.0f}s)
                
                This is taking longer than usual. Possible reasons:
                • Large dataset being processed
                • Complex multi-step operation
                • External service latency
                
                You can stop this operation using the button below.
                """)
            else:
                # Normal progress display
                if self.step_info.get('totalSteps'):
                    current = self.step_info.get('currentStep', 1)
                    total = self.step_info['totalSteps']
                    progress = current / total
                    
                    st.progress(progress)
                    status_text = f"{self.current_phase}"
                    if self.current_tool:
                        status_text += f" - {self.current_tool}"
                    status_text += f" ({elapsed:.1f}s)"
                    st.caption(status_text)
                else:
                    # Simple progress without steps
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        if not self.error_occurred:
                            st.write("⏳")
                    with col2:
                        st.caption(f"{self.current_phase} ({elapsed:.1f}s)")
    
    def handle_event(self, event_type, data):
        """Process incoming SSE events with smart filtering"""
        
        # Handle different event types
        if event_type == 'progress':
            # Extract meaningful information from progress events
            if isinstance(data, dict) and data is not None:
                details = data.get('details', {})
                phase = details.get('phase', '')
                step = data.get('step', '')
                
                # Update step information if available
                if 'currentStep' in details:
                    self.step_info['currentStep'] = details['currentStep']
                    if self.session:
                        self.session.step_info['currentStep'] = details['currentStep']
                if 'totalSteps' in details:
                    self.step_info['totalSteps'] = details['totalSteps']
                    if self.session:
                        self.session.step_info['totalSteps'] = details['totalSteps']
                        
                # Handle specific phases
                if phase in ['llm_request', 'llm_response', 'sql_query', 'sql_result']:
                    self.update_progress(phase=phase.replace('_', ' ').title())
                elif step and 'oracle_full_pipeline' not in step:
                    # Avoid showing the repetitive pipeline messages
                    self.update_progress(phase=step)
                
        elif event_type == 'tool_call_start':
            if isinstance(data, dict) and data is not None:
                tool_name = data.get('tool', '').replace('oracle__', '').replace('_', ' ').title()
                self.current_tool = tool_name
                self.update_progress(phase="Executing", tool=tool_name)
                return f"🔧 {tool_name}\n"
            
        elif event_type == 'tool_call_complete':
            if isinstance(data, dict) and data is not None:
                tool_name = data.get('tool', '').replace('oracle__', '').replace('_', ' ').title()
                if tool_name not in self.completed_tools:
                    self.completed_tools.append(tool_name)
                # Just add a checkmark, don't create new line
                return "✓ "
            
        elif event_type == 'execution_paused':
            if isinstance(data, dict) and data is not None:
                return f"\n⏸️ **{data.get('message', 'Paused')}**\n\n"
            return f"\n⏸️ **Paused**\n\n"
            
        elif event_type == 'agent_question':
            if isinstance(data, dict) and data is not None:
                question = data.get('question', '')
                options = data.get('options', [])
                result = f"\n❓ **{question}**\n"
                if options:
                    for opt in options:
                        result += f"  • {opt}\n"
                return result + "\n"
            
        elif event_type == 'error':
            self.error_occurred = True
            if isinstance(data, dict) and data is not None:
                return f"\n❌ **Error**: {data.get('message', 'Unknown error')}\n"
            elif isinstance(data, str):
                return f"\n❌ **Error**: {data}\n"
            return f"\n❌ **Error**: Unknown error\n"
            
        # Return None for events that shouldn't display immediately
        return None
        
    def clear(self):
        """Clear the progress display"""
        self.progress_placeholder.empty()
        
    def get_summary(self):
        """Get a summary of completed operations"""
        elapsed = time.time() - self.start_time
        summary = f"Completed in {elapsed:.1f}s"
        if self.completed_tools:
            summary += f" • Used {len(self.completed_tools)} tools"
        return summary


def send_to_backend_streaming(messages, message_id):
    """Send messages to Agents-MCP-Host backend with SSE streaming"""
    url = "http://localhost:8080/host/v1/conversations"
    payload = {"messages": messages}
    headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        # Initialize tracking variables
        event_count = 0
        current_event = None
        current_data = []
        stream_id = None
        
        # Process SSE stream line by line
        for line in response.iter_lines():
            if not line:
                # Empty line signals end of an event
                if current_event and current_data:
                    event_count += 1
                    data_str = '\n'.join(current_data)
                    
                    try:
                        # Parse event data
                        if current_event == 'connected':
                            data = json.loads(data_str)
                            stream_id = data.get('streamId', 'unknown')
                            yield ('connected', stream_id, data)
                            
                        elif current_event == 'final_response':
                            data = json.loads(data_str)
                            content = data.get('content', '')
                            yield ('final_response', None, content)
                            return
                            
                        elif current_event == 'error':
                            data = json.loads(data_str)
                            yield ('error', None, data)
                            return
                            
                        elif current_event == 'done':
                            return
                            
                        else:
                            # All other events
                            data = json.loads(data_str)
                            yield (current_event, None, data)
                            
                    except json.JSONDecodeError as e:
                        print(f"[DEBUG] Failed to parse {current_event}: {e}")
                    
                    # Reset for next event
                    current_event = None
                    current_data = []
                continue
            
            # Decode and parse SSE format
            line = line.decode('utf-8') if isinstance(line, bytes) else line
            
            if line.startswith('event: '):
                current_event = line[7:].strip()
            elif line.startswith('data: '):
                current_data.append(line[6:])
                
    except requests.exceptions.ConnectionError:
        yield ('error', None, {'message': 'Backend server not running. Please start Agents-MCP-Host on port 8080.'})
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = e.response.json().get('error', {}).get('message', str(e))
        except:
            error_detail = str(e)
        yield ('error', None, {'message': f'Backend error: {error_detail}'})
    except requests.exceptions.Timeout:
        yield ('error', None, {'message': 'Request timed out. The backend took too long to respond.'})
    except Exception as e:
        yield ('error', None, {'message': f'Unexpected error: {str(e)}'})


def show_technical_details(container, streaming_session, progress_manager):
    """Display technical details in an expander"""
    with container:
        with st.expander("📋 Technical Details", expanded=False):
            st.caption("Event Timeline")
            for event in streaming_session.events[-20:]:  # Last 20 events
                if event['type'] in progress_manager.important_events:
                    st.markdown(f"**{event['timestamp']:.1f}s** - {event['type']}")
                else:
                    st.caption(f"{event['timestamp']:.1f}s - {event['type']}")
            
            if streaming_session.completed_tools:
                st.markdown("**Tools Used:**")
                for tool in streaming_session.completed_tools:
                    st.write(f"• {tool}")


def rebuild_response_display(streaming_session: StreamingSession, container, verbosity: str):
    """Rebuild the response display from stored events"""
    progress_container = container.container()
    response_container = container.container()
    details_container = container.container()
    
    # Initialize progress manager with session data
    progress_manager = ProgressManager(progress_container, streaming_session)
    
    # Get filtered events based on verbosity
    display_events = streaming_session.get_display_events(verbosity)
    
    # Rebuild the display
    response_parts = []
    
    for event in display_events:
        event_type = event['type']
        data = event['data']
        
        if event_type == 'final_response':
            # Clear progress and show final response
            progress_manager.clear()
            
            # Show summary if tools were used
            if streaming_session.completed_tools:
                with response_container:
                    st.caption(f"✅ {progress_manager.get_summary()}")
                    st.markdown("---")
                    
            # Display final response
            with response_container:
                st.markdown(streaming_session.final_response)
                
            # Add details expander if not minimal
            if len(streaming_session.events) > 1 and verbosity != 'Minimal':
                show_technical_details(details_container, streaming_session, progress_manager)
                                
        elif event_type == 'error':
            progress_manager.clear()
            with response_container:
                error_msg = 'Unknown error'
                if isinstance(data, dict) and data is not None:
                    error_msg = data.get('message', 'Unknown error')
                elif isinstance(data, str):
                    error_msg = data
                st.error(error_msg)
                
        else:
            # Process progress event
            if verbosity != 'Minimal':  # Check verbosity before processing
                display_text = progress_manager.handle_event(event_type, data)
                if display_text:
                    response_parts.append(display_text)
                
    # Show accumulated response parts if no final response yet
    if not streaming_session.final_response and not streaming_session.error:
        with response_container:
            if response_parts:
                st.markdown(''.join(response_parts))
                
        # Update progress if still active
        if streaming_session.is_active:
            progress_manager.update_progress()
            
    if streaming_session.final_response:
        return streaming_session.final_response
    elif streaming_session.error:
        return f"Error: {streaming_session.error}"
    else:
        return "Streaming..."


def process_command(command, message_container, message_id):
    """Process user command with improved streaming display and state persistence"""
    
    # Check if we're resuming an existing stream
    if message_id in st.session_state.get('active_streams', {}):
        streaming_session = st.session_state.active_streams[message_id]
        
        # If already completed, just rebuild the display
        if not streaming_session.is_active:
            return rebuild_response_display(streaming_session, message_container, 
                                          st.session_state.get('verbosity', 'Normal'))
    else:
        # Create new streaming session
        streaming_session = StreamingSession(message_id)
        if 'active_streams' not in st.session_state:
            st.session_state.active_streams = {}
        st.session_state.active_streams[message_id] = streaming_session
    
    # Build messages for backend API
    messages = []
    
    # Add system message if it exists
    for msg in st.session_state.messages:
        if msg["role"] == "System":
            messages.append({"role": "system", "content": msg["content"]})
            break
    
    # Add conversation history
    for msg in st.session_state.messages:
        if msg["role"] == "User":
            messages.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "Assistant":
            messages.append({"role": "assistant", "content": msg["content"]})
    
    # Add current user command
    messages.append({"role": "user", "content": command})
    
    # Create containers for response components
    progress_container = message_container.container()
    response_container = message_container.container()
    details_container = message_container.container()
    
    # Initialize progress manager
    progress_manager = ProgressManager(progress_container, streaming_session)
    
    # Container for accumulating the actual response
    response_parts = []
    
    # Get current verbosity
    verbosity = st.session_state.get('verbosity', 'Normal')
    
    # Stream from backend
    for event_type, stream_id, data in send_to_backend_streaming(messages, message_id):
        # Store event in session
        streaming_session.add_event(event_type, data)
        
        if event_type == 'connected':
            st.session_state.stream_id = stream_id
            st.session_state.is_executing = True
            
        elif event_type == 'final_response':
            # Clear progress and show final response
            progress_manager.clear()
            
            # Show summary if tools were used
            if progress_manager.completed_tools:
                with response_container:
                    st.caption(f"✅ {progress_manager.get_summary()}")
                    st.markdown("---")
                    
            # Display final response
            with response_container:
                st.markdown(data)
                
            # Add collapsible details if available and verbosity allows
            if streaming_session.events and verbosity != 'Minimal':
                show_technical_details(details_container, streaming_session, progress_manager)
                
            st.session_state.is_executing = False
            return data
            
        elif event_type == 'error':
            progress_manager.clear()
            with response_container:
                error_msg = 'Unknown error'
                if isinstance(data, dict) and data is not None:
                    error_msg = data.get('message', 'Unknown error')
                elif isinstance(data, str):
                    error_msg = data
                st.error(error_msg)
            st.session_state.is_executing = False
            return f"Error: {error_msg}"
            
        else:
            # Always process events for progress tracking
            display_text = progress_manager.handle_event(event_type, data)
            
            # Show important events based on verbosity level
            if display_text and verbosity != 'Minimal':
                response_parts.append(display_text)
                with response_container:
                    st.markdown(''.join(response_parts))
    
    # If no final response was received
    progress_manager.clear()
    return "No response received"


# System instructions
systems_opening_instructions_to_assistant = '''Be helpful and truthful.'''
assistants_opening_instructions_to_user = '''Okay.'''

# Initialize chat history and state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "System", "content": systems_opening_instructions_to_assistant})
    st.session_state.messages.append({"role": "Assistant", "content": assistants_opening_instructions_to_user})

if "stream_id" not in st.session_state:
    st.session_state.stream_id = None
    
if "is_executing" not in st.session_state:
    st.session_state.is_executing = False

# Clean up old completed streams (older than 5 minutes) and enforce maximum
if "active_streams" in st.session_state:
    current_time = time.time()
    streams_to_remove = []
    
    # Remove old inactive streams
    for msg_id, session in st.session_state.active_streams.items():
        # Mark as inactive if stuck streaming for over 10 minutes
        if session.is_stale(600):
            session.is_active = False
            session.error = "Stream timed out"
        
        # Remove if inactive and older than 5 minutes
        if not session.is_active and (current_time - session.start_time) > 300:
            streams_to_remove.append(msg_id)
    
    # Remove oldest streams if we exceed maximum (keep last 20)
    if len(st.session_state.active_streams) > 20:
        sorted_streams = sorted(st.session_state.active_streams.items(), 
                              key=lambda x: x[1].start_time)
        for msg_id, _ in sorted_streams[:-20]:
            if msg_id not in streams_to_remove:
                streams_to_remove.append(msg_id)
    
    # Perform removal
    for msg_id in streams_to_remove:
        del st.session_state.active_streams[msg_id]

# Display chat messages from history
for i, message in enumerate(st.session_state.messages):
    if message["role"] != "System":  # Don't display system messages
        with st.chat_message(message["role"]):
            if message["role"] == "Assistant":
                # Check if this message has a streaming session
                message_id = message.get('message_id')
                
                if message_id and message_id in st.session_state.get('active_streams', {}):
                    # Rebuild from streaming session with current verbosity
                    msg_container = st.container()
                    streaming_session = st.session_state.active_streams[message_id]
                    rebuild_response_display(streaming_session, msg_container, 
                                           st.session_state.get('verbosity', 'Normal'))
                    
                    # Add controls if this is the most recent active message
                    if i == len(st.session_state.messages) - 1 and streaming_session.is_active:
                        col1, col2, col3 = st.columns([1, 1, 4])
                        with col1:
                            if st.button("🛑 Stop", key=f"stop_{message_id}"):
                                if streaming_session.stream_id:
                                    try:
                                        response = requests.post(
                                            f"http://localhost:8080/host/v1/conversations/{streaming_session.stream_id}/interrupt",
                                            json={"reason": "user_requested"}
                                        )
                                        st.success("Stop request sent!")
                                        streaming_session.is_active = False
                                    except:
                                        st.error("Failed to send stop request")
                else:
                    # Display normally
                    st.markdown(message["content"])
            else:
                st.text(message["role"] + ": " + message["content"])

# Clear button in sidebar
with st.sidebar:
    if st.button("🔄 Clear Chat", key="clear_btn"):
        st.session_state.messages = [
            {"role": "System", "content": systems_opening_instructions_to_assistant},
            {"role": "Assistant", "content": assistants_opening_instructions_to_user}
        ]
        st.session_state.is_executing = False
        st.session_state.stream_id = None
        if "active_streams" in st.session_state:
            st.session_state.active_streams = {}
        st.rerun()
    
    # Verbosity control
    st.markdown("---")
    verbosity = st.select_slider(
        "Progress detail level",
        options=["Minimal", "Normal", "Detailed"],
        value=st.session_state.get('verbosity', 'Normal'),
        help="Control how much progress information is shown"
    )
    
    # Update verbosity in session state
    if verbosity != st.session_state.get('verbosity'):
        st.session_state.verbosity = verbosity
        # Trigger rerun to update display with new verbosity
        st.rerun()

# Chat input
if prompt := st.chat_input("Paste Context or answers or questions..."):
    # Display user message
    with st.chat_message("user"):
        st.text("User: " + prompt)
    
    # Add to history
    st.session_state.messages.append({"role": "User", "content": prompt})
    
    # Display assistant response with streaming
    with st.chat_message("Assistant"):
        message_id = str(uuid.uuid4())
        message_container = st.container()
        
        # Process the command
        full_response = process_command(prompt, message_container, message_id)
        
        # Add response to history with message_id for rebuilding
        st.session_state.messages.append({
            "role": "Assistant", 
            "content": full_response,
            "message_id": message_id
        })
        
        # Add floating controls at bottom of response
        if st.session_state.is_executing:
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("🛑 Stop", key=f"stop_current"):
                    if st.session_state.stream_id:
                        try:
                            response = requests.post(
                                f"http://localhost:8080/host/v1/conversations/{st.session_state.stream_id}/interrupt",
                                json={"reason": "user_requested"}
                            )
                            st.success("Stop request sent!")
                            # Mark the current streaming session as inactive
                            if message_id in st.session_state.active_streams:
                                st.session_state.active_streams[message_id].is_active = False
                        except:
                            st.error("Failed to send stop request")