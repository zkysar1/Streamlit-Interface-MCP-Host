import psutil
import os
import requests
from sseclient import SSEClient
import json
import streamlit as st


st.title("Client Holding Challenge Agent")
st.write("""
### Basic Chat for supporing one challenge at a time? 
Zak Kysar *DRAFT*
""")



def send_to_backend_streaming(messages):
    """Send messages to Agents-MCP-Host backend with SSE streaming"""
    url = "http://localhost:8080/host/v1/conversations"
    payload = {"messages": messages}
    headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
    
    try:
        # Make streaming request
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        # Create SSE client
        client = SSEClient(response)
        
        # Process events
        for event in client.events():
            if event.event == 'tool_call_start':
                data = json.loads(event.data)
                yield f"🔧 {data.get('message', 'Starting tool call...')}\n\n"
            elif event.event == 'tool_call_complete':
                data = json.loads(event.data)
                yield f"✓ Tool completed: {data.get('tool', 'unknown')}\n\n"
            elif event.event == 'progress':
                data = json.loads(event.data)
                step = data.get('step', '')
                message = data.get('message', '')
                elapsed = data.get('elapsed', 0)
                yield f"📊 Progress: {step} - {message} ({elapsed}ms)\n\n"
            elif event.event == 'final_response':
                data = json.loads(event.data)
                content = data.get('content', '')
                yield content
                break
            elif event.event == 'error':
                data = json.loads(event.data)
                yield f"❌ Error: {data.get('message', 'Unknown error')}"
                break
                
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
    except Exception as e:
        yield f"❌ Unexpected error: {str(e)}"


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

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Set base Message to trigger action from user
    st.session_state.messages.append({"role": "System", "content": systems_opening_instructions_to_assistant })
    st.session_state.messages.append({"role": "Assistant", "content": assistants_opening_instructions_to_user })

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] != "System":  # Don't display system messages
        with st.chat_message(message["role"]):
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
    
    # Stream from backend
    return send_to_backend_streaming(messages)



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
        
        # Add complete response to chat history
        st.session_state.messages.append({"role": "Assistant", "content": full_response})
        
    