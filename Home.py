import psutil
import streamlit as st
 
st.write("""# MCP Agent Host Interface""")

st.success("""
🚀 **New Universal Chat Interface Available!**

The new Universal Chat provides a unified interface for all agent types with enhanced features:
- Dynamic agent selection
- Custom agent configuration
- Better user experience
- All existing functionality in one place

**[Go to Universal Chat →](Universal_Chat)**
""")

st.write("""## Available Interfaces""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🚀 Universal Chat (New!)
    - **Oracle DB Q&A Specialist**: Query and analyze database content
    - **SQL Builder**: Generate optimized SQL queries
    - **Direct LLM**: General conversation assistant  
    - **Custom Agent**: User-defined agent with custom backstory
    
    **[Start Chatting →](Universal_Chat)**
    """)

with col2:
    st.markdown("""
    ### 📋 Legacy Interfaces
    - Database Chat (Legacy)
    - SQL Builder Chat (Legacy) 
    - General Chat (Legacy)
    - System Dashboard
    - MCP Tools
    
    *Note: Legacy interfaces redirect to Universal Chat*
    """)

st.divider()
 
st.write("""## System Stats""")

hdd = psutil.disk_usage('/')
st.write("Total Storage: {}gbs".format(hdd.total / (2**30)))
st.write("Total free Storage: {}gbs".format(hdd.free / (2**30)))

cpuCount=psutil.cpu_count(logical=True)
ramUsagePercent=psutil.virtual_memory().percent
totalMemory=psutil.virtual_memory().total/1000000000
st.write("Total memory: {}gbs".format(totalMemory))
st.write("Percent Memory Used: {}%".format(ramUsagePercent))
st.write("Count of CPU Cores: {}".format(cpuCount))