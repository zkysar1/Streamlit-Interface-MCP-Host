import psutil
import os
import requests
import json
import streamlit as st
<<<<<<< HEAD
import time
from datetime import datetime
import uuid
from typing import Dict, List, Optional, Tuple
=======
>>>>>>> parent of 87af339 (Streamlit chat UI: concise progress, floating controls)


st.title("Client Holding Challenge Agent")
st.write("""
### Basic Chat for supporing one challenge at a time? 
Zak Kysar *DRAFT*
""")


<<<<<<< HEAD
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
=======
>>>>>>> parent of 87af339 (Streamlit chat UI: concise progress, floating controls)

def send_to_backend_streaming(messages):
    """Send messages to Agents-MCP-Host backend with SSE streaming"""
    url = "http://localhost:8080/host/v1/conversations"
    payload = {"messages": messages}
    headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
    
    try:
        # Make streaming request
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        # Debug: Check response type
        print(f"[DEBUG] Response type: {type(response)}")
        print(f"[DEBUG] Response status: {response.status_code}")
        print(f"[DEBUG] Response headers: {response.headers}")
        
        # Manual SSE parsing
        event_count = 0
        current_event = None
        current_data = []
        
        # Process SSE stream line by line
        for line in response.iter_lines():
            if not line:
                # Empty line signals end of an event
                if current_event and current_data:
                    # Process the completed event
                    event_count += 1
                    data_str = '\n'.join(current_data)
                    print(f"[DEBUG] Event #{event_count}: type={current_event}, data_length={len(data_str)}")
                    
                    # Parse and handle the event
                    try:
                        # Handle different event types
                        if current_event == 'tool_call_start':
                            data = json.loads(data_str)
<<<<<<< HEAD
                            stream_id = data.get('streamId', 'unknown')
                            yield ('connected', stream_id, data)
=======
                            yield f"🔧 {data.get('message', 'Starting tool call...')}\n\n"
                        elif current_event == 'tool_call_complete':
                            data = json.loads(data_str)
                            yield f"✓ Tool completed: {data.get('tool', 'unknown')}\n\n"
                        elif current_event == 'progress':
                            data = json.loads(data_str)
                            details = data.get('details', {})
                            phase = details.get('phase', '')
>>>>>>> parent of 87af339 (Streamlit chat UI: concise progress, floating controls)
                            
                            # Handle different phases with rich formatting
                            if phase == 'llm_request':
                                messages_sent = details.get('messages', [])
                                yield "\n📤 **Sending to LLM:**\n"
                                for msg in messages_sent[-3:]:  # Show last 3 messages
                                    role = msg.get('role', 'unknown')
                                    content = msg.get('content', '')[:200] + '...' if len(msg.get('content', '')) > 200 else msg.get('content', '')
                                    yield f"  - **{role}**: {content}\n"
                                yield f"  - Total messages: {details.get('messageCount', 0)}\n\n"
                                
                            elif phase == 'llm_response':
                                response_text = details.get('response', '')[:500] + '...' if len(details.get('response', '')) > 500 else details.get('response', '')
                                metadata = details.get('metadata', {})
                                yield "\n📥 **LLM Response:**\n"
                                yield f"  - Response: {response_text}\n"
                                yield f"  - Model: {metadata.get('model', 'unknown')}\n"
                                yield f"  - Tokens: {metadata.get('totalTokens', 0)} (prompt: {metadata.get('promptTokens', 0)}, completion: {metadata.get('completionTokens', 0)})\n\n"
                                
                            elif phase == 'sql_query':
                                query = details.get('query', '')
                                tables = details.get('tables', [])
                                yield "\n🔍 **SQL Query:**\n"
                                yield f"```sql\n{query}\n```\n"
                                if tables:
                                    yield f"  - Tables: {', '.join(tables)}\n"
                                yield f"  - Type: {details.get('queryType', 'unknown')}\n\n"
                                
                            elif phase == 'sql_result':
                                row_count = details.get('rowCount', 0)
                                exec_time = details.get('executionTime', 0)
                                preview = details.get('preview', [])
                                yield "\n📊 **SQL Results:**\n"
                                yield f"  - Rows returned: {row_count}\n"
                                yield f"  - Execution time: {exec_time}ms\n"
                                if preview:
                                    yield "  - Preview:\n"
                                    for i, row in enumerate(preview[:3]):
                                        yield f"    Row {i+1}: {json.dumps(row, indent=2)}\n"
                                yield "\n"
                                
                            elif phase == 'metadata_exploration':
                                table = details.get('table', '')
                                col_count = details.get('columnCount', 0)
                                yield "\n🗂️ **Metadata Exploration:**\n"
                                yield f"  - Table: {table}\n"
                                yield f"  - Columns: {col_count}\n\n"
                                
                            elif phase == 'schema_matching':
                                matched = details.get('matchedTables', [])
                                yield "\n🔗 **Schema Matching:**\n"
                                yield f"  - User query: {details.get('userQuery', '')}\n"
                                yield f"  - Matched tables: {matched}\n\n"
                                
                            elif phase == 'enum_mapping':
                                column = details.get('column', '')
                                mapping_count = details.get('mappingCount', 0)
                                yield "\n🏷️ **Enumeration Mapping:**\n"
                                yield f"  - Column: {column}\n"
                                yield f"  - Mappings found: {mapping_count}\n\n"
                                
                            elif phase == 'tool_selection':
                                strategy = details.get('strategy', '')
                                tools = details.get('selectedTools', [])
                                yield "\n🛠️ **Tool Selection:**\n"
                                yield f"  - Strategy: {strategy}\n"
                                yield f"  - Selected tools: {tools}\n\n"
                                
                            else:
                                # Default progress display
                                step = data.get('step', '')
                                message = data.get('message', '')
                                elapsed = data.get('elapsed', 0)
                                yield f"📊 Progress: {step} - {message} ({elapsed}ms)\n\n"
                                
                        elif current_event == 'execution_paused':
                            data = json.loads(data_str)
                            yield f"\n⏸️ **Execution Paused**\n"
                            yield f"Reason: {data.get('reason', 'User requested')}\n"
                            yield f"{data.get('message', 'Waiting for your input...')}\n\n"
                            
                        elif current_event == 'agent_question':
                            data = json.loads(data_str)
                            question = data.get('question', '')
                            options = data.get('options', [])
                            yield f"\n❓ **Agent Question:**\n"
                            yield f"{question}\n"
                            if options:
                                yield "Options:\n"
                                for opt in options:
                                    yield f"  - {opt}\n"
                            yield "\n"
                            
                        elif current_event == 'connected':
                            # Handle connection event
                            try:
                                data = json.loads(data_str)
                                stream_id = data.get('streamId', 'unknown')
                                yield f"🔗 Connected to stream: {stream_id}\n\n"
                            except:
                                pass
                        elif current_event == 'final_response':
<<<<<<< HEAD
                            data = json.loads(data_str)
                            content = data.get('content', '')
                            yield ('final_response', None, content)
                            return
                            
=======
                            try:
                                data = json.loads(data_str)
                                content = data.get('content', '')
                                yield content
                                return  # Exit the generator
                            except json.JSONDecodeError as e:
                                yield f"❌ Failed to parse final response: {e}\n"
                                yield f"Raw data: {data_str}\n"
                                return
>>>>>>> parent of 87af339 (Streamlit chat UI: concise progress, floating controls)
                        elif current_event == 'error':
                            try:
                                data = json.loads(data_str)
                                yield f"❌ Error: {data.get('message', 'Unknown error')}"
                            except:
                                yield f"❌ Error event with unparseable data: {data_str}"
                            return
                        elif current_event == 'done':
                            # Handle stream completion
                            try:
                                data = json.loads(data_str)
                                print(f"[DEBUG] Stream completed: {data.get('message', 'Done')}")
                            except:
                                pass
                            return
                        else:
                            # Unknown event type
                            print(f"[DEBUG] Unknown event type: {current_event}")
                    except Exception as e:
                        print(f"[DEBUG] Error handling event: {e}")
                        print(f"[DEBUG] Event type: {current_event}, Data: {data_str[:200]}")
                    
                    # Reset for next event
                    current_event = None
                    current_data = []
                continue
            
            # Decode the line
            line = line.decode('utf-8') if isinstance(line, bytes) else line
            
            # Parse SSE format
            if line.startswith('event: '):
                current_event = line[7:].strip()
            elif line.startswith('data: '):
                current_data.append(line[6:])
                
    except requests.exceptions.ConnectionError:
        yield "❌ Backend server not running. Please start Agents-MCP-Host on port 8080."
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = e.response.json().get('error', {}).get('message', str(e))
        except:
            error_detail = str(e)
        yield f"❌ Backend error: {error_detail}"
    except requests.exceptions.Timeout:
        yield "❌ Request timed out. The backend took too long to respond."
    except json.JSONDecodeError as e:
        yield f"❌ Error parsing JSON: {e}\nRaw data: {data_str[:200] if 'data_str' in locals() else 'None'}"
    except Exception as e:
        import traceback
        yield f"❌ Unexpected error: {str(e)}\n{traceback.format_exc()}"


<<<<<<< HEAD
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
=======
# create opening message exchanges
## There are two poeple talking to the llm, the user and the systm.  There is a fourth person in the chat as well called prompt that only regertates prompts.  
#systems_opening_instructions_to_assistant = '''Folllow by these rules:
#1: Proper Json is required.  When outputtting json, eensure that it can compute without errors and with closing brakets.
#2: Ask questions about additional json data points you need.
#
#Your end goal is to output full json data objects.'''

systems_opening_instructions_to_assistant = '''Be helpful and truthful.'''



assistants_opening_instructions_to_user = '''Okay.'''


# I have a client challenge about the is restricted data point for these two cusips: 037833DT4 and 037833DT5. 
# { "clientId": "APGEMINI", "portfolio": "my portfolio", "dataAsOfDate": "2023-05-06", "dataPointNameBeingChallenged": "isRestricted", "entityId": "037833DT4", "marketValuePosition": "10000", "rats": ".05", "tmpi": ".02"}

# Initialize chat history and state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Set base Message to trigger action from user
    st.session_state.messages.append({"role": "System", "content": systems_opening_instructions_to_assistant })
    st.session_state.messages.append({"role": "Assistant", "content": assistants_opening_instructions_to_user })

if "stream_id" not in st.session_state:
    st.session_state.stream_id = None
>>>>>>> parent of 87af339 (Streamlit chat UI: concise progress, floating controls)
    
if "is_executing" not in st.session_state:
    st.session_state.is_executing = False

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] != "System":  # Don't display system messages
        with st.chat_message(message["role"]):
            # Use markdown for better formatting
            if message["role"] == "Assistant":
                st.markdown(message["content"])
            else:
                st.text(message["role"]+": "+message["content"])




# process user command with streaming
def process_command(command):
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
    
<<<<<<< HEAD
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
=======
    # Stream from backend
    return send_to_backend_streaming(messages)
>>>>>>> parent of 87af339 (Streamlit chat UI: concise progress, floating controls)


# Add stop button and clear button
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("🛑 Stop", disabled=not st.session_state.is_executing, key="stop_btn"):
        if st.session_state.stream_id:
            # Send interrupt request
            try:
                response = requests.post(
                    f"http://localhost:8080/host/v1/conversations/{st.session_state.stream_id}/interrupt",
                    json={"reason": "user_requested"}
                )
                st.success("Stop request sent!")
            except:
                st.error("Failed to send stop request")

<<<<<<< HEAD
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
=======
with col2:
    if st.button("🔄 Clear", key="clear_btn"):
>>>>>>> parent of 87af339 (Streamlit chat UI: concise progress, floating controls)
        st.session_state.messages = [
            {"role": "System", "content": systems_opening_instructions_to_assistant},
            {"role": "Assistant", "content": assistants_opening_instructions_to_user}
        ]
<<<<<<< HEAD
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
=======
        st.rerun()
>>>>>>> parent of 87af339 (Streamlit chat UI: concise progress, floating controls)

# React to user input
if prompt := st.chat_input("Paste Context or answers or questions. . ."):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.text("User: "+prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "User", "content": prompt})
    
    # Display assistant response with streaming
    with st.chat_message("Assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Stream the response
        for chunk in process_command(prompt):
            full_response += chunk
            response_placeholder.markdown("Assistant: " + full_response)
        
<<<<<<< HEAD
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
=======
        # Add complete response to chat history
        st.session_state.messages.append({"role": "Assistant", "content": full_response})
        
    
>>>>>>> parent of 87af339 (Streamlit chat UI: concise progress, floating controls)
