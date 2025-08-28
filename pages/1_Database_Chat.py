import psutil
import os
import requests
import json
import streamlit as st


st.title("📊 Database Chat")
st.write("""
### Query your Oracle database using natural language
**Host:** Oracle DB Answerer (`oracledbanswerer`)
""")



def send_to_backend_streaming(messages):
    """Send messages to Agents-MCP-Host backend with SSE streaming"""
    url = "http://localhost:8080/host/v1/conversations"
    payload = {"messages": messages, "host": "oracledbanswerer"}
    headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
    
    # Set execution state
    st.session_state.db_chat_is_executing = True
    
    try:
        # Make streaming request
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=300)
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
                            yield f"🔧 {data.get('message', 'Starting tool call...')}\n\n"
                        elif current_event == 'tool_call_complete':
                            data = json.loads(data_str)
                            yield f"✓ Tool completed: {data.get('tool', 'unknown')}\n\n"
                        elif current_event == 'progress':
                            data = json.loads(data_str)
                            details = data.get('details', {})
                            phase = details.get('phase', '')
                            
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
                                # Store stream ID in session state
                                st.session_state.db_chat_stream_id = stream_id
                                yield f"🔗 Connected to stream: {stream_id}\n\n"
                            except Exception as e:
                                print(f"[DEBUG] Error parsing connected event: {e}")
                        elif current_event == 'final_response':
                            try:
                                data = json.loads(data_str)
                                content = data.get('content', '')
                                yield content
                                # Clear execution state on completion
                                st.session_state.db_chat_is_executing = False
                                st.session_state.db_chat_stream_id = None
                                return  # Exit the generator
                            except json.JSONDecodeError as e:
                                yield f"❌ Failed to parse final response: {e}\n"
                                yield f"Raw data: {data_str}\n"
                                # Clear execution state on error
                                st.session_state.db_chat_is_executing = False
                                st.session_state.db_chat_stream_id = None
                                return
                        elif current_event == 'error':
                            try:
                                data = json.loads(data_str)
                                yield f"❌ Error: {data.get('message', 'Unknown error')}"
                            except:
                                yield f"❌ Error event with unparseable data: {data_str}"
                            # Clear execution state on error
                            st.session_state.db_chat_is_executing = False
                            st.session_state.db_chat_stream_id = None
                            return
                        elif current_event == 'done':
                            # Handle stream completion
                            try:
                                data = json.loads(data_str)
                                print(f"[DEBUG] Stream completed: {data.get('message', 'Done')}")
                            except Exception as e:
                                print(f"[DEBUG] Error parsing done event: {e}")
                            # Clear execution state on done
                            st.session_state.db_chat_is_executing = False
                            st.session_state.db_chat_stream_id = None
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
        st.session_state.db_chat_is_executing = False
        st.session_state.db_chat_stream_id = None
        yield "❌ Backend server not running. Please start Agents-MCP-Host on port 8080."
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = e.response.json().get('error', {}).get('message', str(e))
        except:
            error_detail = str(e)
        st.session_state.db_chat_is_executing = False
        st.session_state.db_chat_stream_id = None
        yield f"❌ Backend error: {error_detail}"
    except requests.exceptions.Timeout:
        st.session_state.db_chat_is_executing = False
        st.session_state.db_chat_stream_id = None
        yield "❌ Request timed out. The backend took too long to respond."
    except json.JSONDecodeError as e:
        st.session_state.db_chat_is_executing = False
        st.session_state.db_chat_stream_id = None
        yield f"❌ Error parsing JSON: {e}\nRaw data: {data_str[:200] if 'data_str' in locals() else 'None'}"
    except Exception as e:
        import traceback
        st.session_state.db_chat_is_executing = False
        st.session_state.db_chat_stream_id = None
        yield f"❌ Unexpected error: {str(e)}\n{traceback.format_exc()}"


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
if "db_chat_messages" not in st.session_state:
    st.session_state.db_chat_messages = []
    # Set base Message to trigger action from user
    st.session_state.db_chat_messages.append({"role": "system", "content": systems_opening_instructions_to_assistant })
    st.session_state.db_chat_messages.append({"role": "assistant", "content": assistants_opening_instructions_to_user })

if "db_chat_stream_id" not in st.session_state:
    st.session_state.db_chat_stream_id = None
    
if "db_chat_is_executing" not in st.session_state:
    st.session_state.db_chat_is_executing = False

# Display chat messages from history on app rerun
for message in st.session_state.db_chat_messages:
    if message["role"] != "system":  # Don't display system messages
        with st.chat_message(message["role"]):
            # Use markdown for all messages
            st.markdown(message["content"])




# process user command with streaming
def process_command(command):
    # Build messages for backend API
    messages = []
    
    # Add all messages (system, user, assistant) to the API request
    for msg in st.session_state.db_chat_messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current user command
    messages.append({"role": "user", "content": command})
    
    # Stream from backend
    return send_to_backend_streaming(messages)


# Add stop button and clear button
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("🛑 Stop", disabled=not st.session_state.db_chat_is_executing, key="stop_btn"):
        if st.session_state.db_chat_stream_id:
            # Send interrupt request
            try:
                response = requests.post(
                    f"http://localhost:8080/host/v1/conversations/{st.session_state.db_chat_stream_id}/interrupt",
                    json={"reason": "user_requested"}
                )
                st.success("Stop request sent!")
                # Clear execution state after interrupt
                st.session_state.db_chat_is_executing = False
                st.session_state.db_chat_stream_id = None
            except Exception as e:
                st.error(f"Failed to send stop request: {str(e)}")

with col2:
    if st.button("🔄 Clear", key="clear_btn"):
        st.session_state.db_chat_messages = [
            {"role": "system", "content": systems_opening_instructions_to_assistant},
            {"role": "assistant", "content": assistants_opening_instructions_to_user}
        ]
        # Also clear execution state
        st.session_state.db_chat_is_executing = False
        st.session_state.db_chat_stream_id = None
        st.rerun()

# React to user input
if prompt := st.chat_input("Paste Context or answers or questions. . ."):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.db_chat_messages.append({"role": "user", "content": prompt})
    
    # Display assistant response with streaming
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Stream the response
        for chunk in process_command(prompt):
            full_response += chunk
            response_placeholder.markdown(full_response)
        
        # Add complete response to chat history
        st.session_state.db_chat_messages.append({"role": "assistant", "content": full_response})
        
    