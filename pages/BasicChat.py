import psutil
import os
from openai import OpenAI
import streamlit as st


st.title("Client Holding Challenge Agent")
st.write("""
### Basic Chat for supporing one challenge at a time? 
Zak Kysar *DRAFT*
""")



@st.cache_resource
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY environment variable not set!")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()


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






# process user command
def process_command(command):
    # Build messages for OpenAI API
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
    
    # Send command to the model
    with st.spinner('llm working on a response...'):
        completion = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=messages,
            max_tokens=400,
            temperature=0.2
        )
        response = completion.choices[0].message.content
        return response



# React to user input
if prompt := st.chat_input("Paste Context or answers or questions. . ."):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.text("User: "+prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "User", "content": prompt})
    # Send this to the llm
    llmResponse= process_command(prompt)
    # Display assistant response in chat message container
    with st.chat_message("Assistant"):
        st.text("Assistant: "+llmResponse)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "Assistant", "content": llmResponse})
        
    