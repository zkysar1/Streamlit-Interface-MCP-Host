import psutil
import os
import requests
import json
import streamlit as st
import time
from datetime import datetime
import uuid


st.title("Client Holding Challenge Agent")
st.write("""
### Basic Chat for supporing one challenge at a time? 
Zak Kysar *DRAFT*
""")


class ProgressManager:
    """Manages progress display with minimal verbosity and smart updates"""
    
    def __init__(self, container):
        self.container = container
        self.progress_placeholder = container.empty()
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
        
        # Verbose event types to collect but not display immediately
        self.verbose_events = {
            'tool_routing', 'tool_execution', 'tool_analysis',
            'intent_analysis', 'tool_selection'
        }
        
        # Details for collapsible section
        self.details = []
        
    def update_progress(self, phase=None, tool=None):
        """Update the progress display in place"""
        elapsed = time.time() - self.start_time
        
        if phase:
            self.current_phase = phase
        if tool:
            self.current_tool = tool
            
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
        
        # Always collect details for debugging
        self.details.append({
            'time': time.time() - self.start_time,
            'type': event_type,
            'data': data
        })
        
        # Handle different event types
        if event_type == 'progress':
            # Extract meaningful information from progress events
            details = data.get('details', {})
            phase = details.get('phase', '')
            step = data.get('step', '')
            
            # Update step information if available
            if 'currentStep' in details:
                self.step_info['currentStep'] = details['currentStep']
            if 'totalSteps' in details:
                self.step_info['totalSteps'] = details['totalSteps']
                
            # Handle specific phases
            if phase in ['llm_request', 'llm_response', 'sql_query', 'sql_result']:
                self.update_progress(phase=phase.replace('_', ' ').title())
            elif step and 'oracle_full_pipeline' not in step:
                # Avoid showing the repetitive pipeline messages
                self.update_progress(phase=step)
                
        elif event_type == 'tool_call_start':
            tool_name = data.get('tool', '').replace('oracle__', '').replace('_', ' ').title()
            self.current_tool = tool_name
            self.update_progress(phase="Executing", tool=tool_name)
            return f"🔧 {tool_name}\n"
            
        elif event_type == 'tool_call_complete':
            tool_name = data.get('tool', '').replace('oracle__', '').replace('_', ' ').title()
            self.completed_tools.append(tool_name)
            # Just add a checkmark, don't create new line
            return "✓ "
            
        elif event_type == 'execution_paused':
            return f"\n⏸️ **{data.get('message', 'Paused')}**\n\n"
            
        elif event_type == 'agent_question':
            question = data.get('question', '')
            options = data.get('options', [])
            result = f"\n❓ **{question}**\n"
            if options:
                for opt in options:
                    result += f"  • {opt}\n"
            return result + "\n"
            
        elif event_type == 'error':
            self.error_occurred = True
            return f"\n❌ **Error**: {data.get('message', 'Unknown error')}\n"
            
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
                            yield ('connected', stream_id, None)
                            
                        elif current_event == 'final_response':
                            data = json.loads(data_str)
                            yield ('final_response', None, data.get('content', ''))
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


def process_command(command, message_container, message_id):
    """Process user command with improved streaming display"""
    
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
    progress_manager = ProgressManager(progress_container)
    
    # Container for accumulating the actual response
    response_parts = []
    
    # Track if we've shown any tool output
    tool_output_shown = False
    
    # Stream from backend
    for event_type, stream_id, data in send_to_backend_streaming(messages, message_id):
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
            if progress_manager.details and st.session_state.get('verbosity', 'Normal') != 'Minimal':
                with details_container:
                    with st.expander("📋 Technical Details", expanded=False):
                        st.caption("Event Timeline")
                        for detail in progress_manager.details[-20:]:  # Show last 20 events
                            event_type = detail['type']
                            elapsed = detail['time']
                            
                            # Format based on event type
                            if event_type in progress_manager.important_events:
                                st.markdown(f"**{elapsed:.1f}s** - {event_type}")
                            else:
                                st.caption(f"{elapsed:.1f}s - {event_type}")
                        
                        # Show tools used
                        if progress_manager.completed_tools:
                            st.markdown("**Tools Used:**")
                            for tool in progress_manager.completed_tools:
                                st.write(f"• {tool}")
                
            st.session_state.is_executing = False
            return data
            
        elif event_type == 'error':
            progress_manager.clear()
            with response_container:
                st.error(data.get('message', 'Unknown error'))
            st.session_state.is_executing = False
            return f"Error: {data.get('message', 'Unknown error')}"
            
        else:
            # Process progress event based on verbosity
            verbosity = st.session_state.get('verbosity', 'Normal')
            
            # Always process events for progress tracking
            display_text = progress_manager.handle_event(event_type, data)
            
            # Show important events based on verbosity level
            if display_text and verbosity != 'Minimal':
                tool_output_shown = True
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

# Display chat messages from history
for i, message in enumerate(st.session_state.messages):
    if message["role"] != "System":  # Don't display system messages
        with st.chat_message(message["role"]):
            if message["role"] == "Assistant":
                # Create container for message with controls
                msg_container = st.container()
                
                # Display message content
                with msg_container:
                    st.markdown(message["content"])
                    
                # Add controls at bottom of this specific message
                if i == len(st.session_state.messages) - 1 and st.session_state.is_executing:
                    # Only show controls for the most recent message if executing
                    col1, col2, col3 = st.columns([1, 1, 4])
                    with col1:
                        if st.button("🛑 Stop", key=f"stop_{i}"):
                            if st.session_state.stream_id:
                                try:
                                    response = requests.post(
                                        f"http://localhost:8080/host/v1/conversations/{st.session_state.stream_id}/interrupt",
                                        json={"reason": "user_requested"}
                                    )
                                    st.success("Stop request sent!")
                                except:
                                    st.error("Failed to send stop request")
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
        st.rerun()
    
    # Verbosity control
    st.markdown("---")
    verbosity = st.select_slider(
        "Progress detail level",
        options=["Minimal", "Normal", "Detailed"],
        value="Normal",
        help="Control how much progress information is shown"
    )
    st.session_state.verbosity = verbosity

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
        
        # Add response to history
        st.session_state.messages.append({"role": "Assistant", "content": full_response})
        
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
                        except:
                            st.error("Failed to send stop request")