import requests
import json
import streamlit as st

# Base URL for backend API
BASE_URL = "http://localhost:8080"


# Predefined Agent Configurations
AGENT_CONFIGS = {
    "Oracle DB Answerer": {
        "backstory": "You are a senior Oracle database analyst with 15+ years of experience. You have deep knowledge of Oracle SQL, PL/SQL, database administration, performance tuning, and data modeling. You excel at understanding business requirements and translating them into efficient database queries. You always strive to provide data-driven answers by executing queries and analyzing actual results.",
        "guidance": "Always execute queries to provide accurate, data-driven answers. Use the full pipeline (depth 10) when possible. Explore schema, analyze queries, generate SQL, validate, optimize, execute, and format results. Be thorough and precise. When users ask questions, find the actual data to answer them."
    },
    "Oracle SQL Builder": {
        "backstory": "You are an Oracle SQL generation specialist focused on creating perfectly optimized queries. You understand complex SQL patterns, window functions, CTEs, hierarchical queries, and Oracle-specific features. Your expertise lies in query construction and optimization, but you do not execute queries - you only generate and validate them.",
        "guidance": "Focus on SQL generation and validation only. Never execute queries. Stop at pipeline level 5 (validation). Provide detailed explanations of the SQL you generate, including what each part does and why it's structured that way. Suggest indexes and optimization strategies but don't run the queries."
    },
    "Direct LLM No Tool": {
        "backstory": "You are a helpful general assistant without access to any database or external tools. You can only provide information based on your training data and general knowledge. You cannot execute queries, access databases, or use any MCP tools.",
        "guidance": "Do not use any database tools or MCP clients. Pipeline depth should be 0 - no manager execution. Respond only with general knowledge and explanations. If asked about specific data, explain that you cannot access databases and suggest what kinds of queries would be needed."
    },
    "Free Agent": {
        "backstory": None,  # User will provide
        "guidance": None     # User will provide
    }
}

# Initialize session state
if "universal_chat_messages" not in st.session_state:
    st.session_state.universal_chat_messages = []

if "universal_chat_stream_id" not in st.session_state:
    st.session_state.universal_chat_stream_id = None
    
if "universal_chat_is_executing" not in st.session_state:
    st.session_state.universal_chat_is_executing = False

if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = "Oracle DB Answerer"

if "custom_backstory" not in st.session_state:
    st.session_state.custom_backstory = ""
    
if "custom_guidance" not in st.session_state:
    st.session_state.custom_guidance = ""


st.title("🚀 Universal Chat")

# Simple agent selection
selected_agent = st.selectbox(
    "Select agent:",
    options=list(AGENT_CONFIGS.keys()),
    index=list(AGENT_CONFIGS.keys()).index(st.session_state.selected_agent),
    key="agent_selector"
)

# Update selection if changed
if selected_agent != st.session_state.selected_agent:
    st.session_state.selected_agent = selected_agent
    st.session_state.universal_chat_messages = []
    st.session_state.universal_chat_stream_id = None
    st.session_state.universal_chat_is_executing = False

# Display agent configuration for Free Agent only
if selected_agent == "Free Agent":
    st.divider()
    # Custom input fields for Free Agent
    st.subheader("🎯 Custom Agent Configuration")
    st.markdown("Define your own agent by providing backstory and guidance:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        custom_backstory = st.text_area(
            "Backstory (Required)",
            value=st.session_state.custom_backstory,
            placeholder="Define your agent's personality, expertise, and background...",
            height=150,
            key="custom_backstory_input",
            help="Describe what kind of assistant this should be"
        )
        st.session_state.custom_backstory = custom_backstory
    
    with col2:
        custom_guidance = st.text_area(
            "Guidance and Guardrails (Required)",
            value=st.session_state.custom_guidance,
            placeholder="Define behavioral guidelines and rules for your agent...",
            height=150,
            key="custom_guidance_input",
            help="Provide specific guidance on how the agent should behave"
        )
        st.session_state.custom_guidance = custom_guidance
    
    # Validation warning
    if not custom_backstory or not custom_guidance:
        st.warning("⚠️ Both Backstory and Guidance are required for Free Agent")

# Simple divider
st.markdown("---")

def send_to_backend_streaming(messages, backstory, guidance):
    """Send messages to Agents-MCP-Host backend with SSE streaming"""
    url = f"{BASE_URL}/host/v1/conversations"
    
    # Build payload with backstory and guidance for UniversalHost
    payload = {
        "messages": messages
    }
    
    # Add backstory and guidance if provided
    if backstory:
        payload["backstory"] = backstory
    if guidance:
        payload["guidance"] = guidance
    
    headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
    
    # Set execution state
    st.session_state.universal_chat_is_executing = True
    
    try:
        # Make streaming request
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=300)
        response.raise_for_status()
        
        # Manual SSE parsing
        current_event = None
        current_data = []
        
        # Process SSE stream line by line
        for line in response.iter_lines():
            if not line:
                # Empty line signals end of an event
                if current_event and current_data:
                    # Process the completed event
                    data_str = '\n'.join(current_data)
                    
                    # Parse and handle the event - simplified for cleaner output
                    try:
                        if current_event == 'connected':
                            # Handle connection event silently
                            data = json.loads(data_str)
                            stream_id = data.get('sessionId', 'unknown')
                            st.session_state.universal_chat_stream_id = stream_id
                            
                        elif current_event == 'progress':
                            # Only show SQL queries and results
                            data = json.loads(data_str)
                            details = data.get('details', {})
                            phase = details.get('phase', '')
                            
                            if phase == 'sql_query':
                                query = details.get('query', '')
                                if query:
                                    yield f"\n```sql\n{query}\n```\n"
                                    
                            elif phase == 'sql_result':
                                row_count = details.get('rowCount', 0)
                                preview = details.get('preview', [])
                                if row_count > 0:
                                    yield f"\nFound {row_count} rows:\n"
                                    if preview:
                                        for row in preview[:3]:
                                            yield f"{json.dumps(row, indent=2)}\n"
                                        if row_count > 3:
                                            yield f"... and {row_count - 3} more rows\n"
                                            
                        elif current_event == 'final':
                            data = json.loads(data_str)
                            content = data.get('content', '')
                            yield content
                            # Clear execution state on completion
                            st.session_state.universal_chat_is_executing = False
                            st.session_state.universal_chat_stream_id = None
                            return  # Exit the generator
                            
                        elif current_event == 'error':
                            data = json.loads(data_str)
                            yield f"❌ Error: {data.get('message', 'Unknown error')}"
                            # Clear execution state on error
                            st.session_state.universal_chat_is_executing = False
                            st.session_state.universal_chat_stream_id = None
                            return
                            
                    except Exception as e:
                        print(f"[DEBUG] Error handling event: {e}")
                    
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
        st.session_state.universal_chat_is_executing = False
        st.session_state.universal_chat_stream_id = None
        yield "❌ Backend server not running. Please start Agents-MCP-Host on port 8080."
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = e.response.json().get('error', {}).get('message', str(e))
        except:
            error_detail = str(e)
        st.session_state.universal_chat_is_executing = False
        st.session_state.universal_chat_stream_id = None
        yield f"❌ Backend error: {error_detail}"
    except requests.exceptions.Timeout:
        st.session_state.universal_chat_is_executing = False
        st.session_state.universal_chat_stream_id = None
        yield "❌ Request timed out. The backend took too long to respond."
    except Exception as e:
        import traceback
        st.session_state.universal_chat_is_executing = False
        st.session_state.universal_chat_stream_id = None
        yield f"❌ Unexpected error: {str(e)}\n{traceback.format_exc()}"


def process_command(command):
    """Build messages for backend API and stream the response"""
    # Get configuration for selected agent
    config = AGENT_CONFIGS[st.session_state.selected_agent]
    
    # Determine backstory and guidance based on selected agent
    if st.session_state.selected_agent == "Free Agent":
        # Validate that custom fields are provided
        if not st.session_state.custom_backstory or not st.session_state.custom_guidance:
            yield "❌ Error: Both Backstory and Guidance are required for Free Agent. Please provide them above."
            return
        if st.session_state.custom_backstory.strip() == "" or st.session_state.custom_guidance.strip() == "":
            yield "❌ Error: Backstory and Guidance cannot be empty. Please provide meaningful values."
            return
        backstory = st.session_state.custom_backstory.strip()
        guidance = st.session_state.custom_guidance.strip()
    else:
        # Use predefined backstory and guidance
        backstory = config["backstory"]
        guidance = config["guidance"]
    
    # Build messages for backend API
    messages = []
    
    # Add all messages to the API request
    for msg in st.session_state.universal_chat_messages:
        if msg["role"] != "system":  # Don't send system messages to backend
            messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current user command
    messages.append({"role": "user", "content": command})
    
    # Stream from backend with backstory and guidance
    return send_to_backend_streaming(messages, backstory, guidance)


# Simple clear button
if st.button("🔄 Clear Chat", key="clear_btn"):
    st.session_state.universal_chat_messages = []
    st.session_state.universal_chat_is_executing = False
    st.session_state.universal_chat_stream_id = None
    st.rerun()

# Display chat messages from history on app rerun
for message in st.session_state.universal_chat_messages:
    if message["role"] != "system":  # Don't display system messages
        with st.chat_message(message["role"]):
            # Use markdown for all messages
            st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask me anything..."):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.universal_chat_messages.append({"role": "user", "content": prompt})
    
    # Display assistant response with streaming
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Stream the response
        for chunk in process_command(prompt):
            full_response += chunk
            response_placeholder.markdown(full_response)
        
        # Add complete response to chat history
        st.session_state.universal_chat_messages.append({"role": "assistant", "content": full_response})