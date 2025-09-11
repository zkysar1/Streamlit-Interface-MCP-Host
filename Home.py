import streamlit as st
import requests

# Base URL for backend API
BASE_URL = "http://localhost:8080"

# Page configuration
st.set_page_config(
    page_title="SQL Query Assistant",
    page_icon="🎯",
    layout="wide"
)

# Hero Section
st.title("🎯 SQL Query Assistant")
st.subheader("Transform Natural Language Questions into Database Insights")

st.info("""
This intelligent system understands your data questions and progressively builds 
the perfect SQL query through 6 smart milestones. Each step is transparent and 
shareable, giving you full visibility into how your answer is generated.
""")

# Milestone Pipeline Visualization
st.divider()
st.header("📊 The 6-Milestone Pipeline")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 1️⃣ Intent Extraction
    *Understanding what you're really asking*
    
    The system analyzes your question to extract the core intent, 
    identifying what type of data you need and how it should be presented.
    
    ---
    
    ### 2️⃣ Schema Exploration  
    *Finding the right tables for your question*
    
    Explores the database schema to identify relevant tables and 
    relationships that contain the data you're looking for.
    """)

with col2:
    st.markdown("""
    ### 3️⃣ Data Analysis
    *Examining columns and data patterns*
    
    Analyzes table columns, data types, and statistics to understand 
    the structure and content of your data.
    
    ---
    
    ### 4️⃣ SQL Generation
    *Creating the optimal query*
    
    Generates a precise, optimized SQL statement based on all 
    the information gathered from previous steps.
    """)
    
with col3:
    st.markdown("""
    ### 5️⃣ Query Execution
    *Running and retrieving results*
    
    Executes the generated SQL query against the database and 
    retrieves the actual data results.
    
    ---
    
    ### 6️⃣ Natural Response
    *Formatting your answer clearly*
    
    Transforms the raw query results into a clear, natural language 
    answer that directly addresses your original question.
    """)

# How It Works Section
st.divider()
st.header("🔧 How It Works")

tab1, tab2, tab3 = st.tabs(["🚀 Quick Start", "🎯 Milestone Control", "📝 Examples"])

with tab1:
    st.markdown("""
    ### Getting Started is Simple
    
    1. **Provide Context (Backstory)**: Define your assistant's expertise and role
       - Example: *"You are a senior data analyst specializing in sales metrics"*
    
    2. **Set Guidelines (Guidance)**: Add any specific rules or constraints
       - Example: *"Always validate data quality and provide confidence levels"*
    
    3. **Ask Your Question**: Type your natural language query
       - Example: *"What were our top 5 products by revenue last quarter?"*
    
    4. **Watch Progress**: See results from each milestone as they complete
       - The system will show you what it discovers at each step
       - You'll see the intent, schema, SQL, and final results
    
    The system automatically determines how many milestones to execute based on your context and question!
    """)

with tab2:
    st.markdown("""
    ### Intelligent Milestone Selection
    
    The system intelligently decides which milestone to stop at based on three factors:
    
    #### 1. **Backstory** - Defines the assistant's role and expertise
    - Data Analyst → Full pipeline (all 6 milestones)
    - SQL Developer → Stop at SQL generation (milestone 4)
    - Schema Explorer → Stop at schema discovery (milestone 2)
    
    #### 2. **Guidance** - Sets behavioral rules and constraints
    - *"Execute queries and provide results"* → Goes to milestone 6
    - *"Only generate SQL, don't execute"* → Stops at milestone 4
    - *"Just analyze the intent"* → Stops at milestone 1
    
    #### 3. **Your Query** - The actual question determines depth
    - *"How many..."* → Full execution for counting
    - *"Show me the SQL for..."* → SQL generation only
    - *"What tables contain..."* → Schema exploration only
    
    ### Milestone Stop Examples
    
    | Query Pattern | Target Milestone | What You Get |
    |--------------|------------------|--------------|
    | "What does this mean..." | 1 - Intent | Clear understanding of the question |
    | "What tables have..." | 2 - Schema | List of relevant tables |
    | "What columns..." | 3 - Data Stats | Column analysis and statistics |
    | "Generate SQL for..." | 4 - SQL Gen | Complete SQL statement |
    | "Execute query..." | 5 - Execution | Raw data results |
    | "How many..." / "What is..." | 6 - Natural | Natural language answer |
    """)

with tab3:
    st.markdown("""
    ### Example Scenarios
    
    #### 📊 Example 1: Sales Analysis
    **Backstory**: "You are a sales data analyst"  
    **Guidance**: "Provide actionable insights with data"  
    **Query**: "What were our best performing products last month?"  
    **Result**: Full 6-milestone execution with natural language summary
    
    ---
    
    #### 🔍 Example 2: SQL Development
    **Backstory**: "You are a SQL developer"  
    **Guidance**: "Generate optimized queries only, don't execute"  
    **Query**: "Create a query to find duplicate customer records"  
    **Result**: Stops at milestone 4 with validated SQL statement
    
    ---
    
    #### 📋 Example 3: Schema Discovery
    **Backstory**: "You are a database architect"  
    **Guidance**: "Focus on schema and structure only"  
    **Query**: "What tables contain order information?"  
    **Result**: Stops at milestone 2 with schema details
    
    ---
    
    #### 💡 Example 4: Intent Clarification
    **Backstory**: "You are a requirements analyst"  
    **Guidance**: "Extract and clarify intent only"  
    **Query**: "I need to see customer trends"  
    **Result**: Stops at milestone 1 with detailed intent analysis
    """)

# Quick Start Section
st.divider()
st.header("🚀 Ready to Start?")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Start with Guided Setup
    Configure your backstory and guidance with helpful templates
    """)
    if st.button("🎯 Start with Guided Setup", type="primary", use_container_width=True):
        st.switch_page("pages/0_Universal_Chat.py")
        
with col2:
    st.markdown("""
    ### Jump Directly to Chat
    Start chatting immediately with default settings
    """)
    if st.button("💬 Jump to Chat", use_container_width=True):
        st.switch_page("pages/0_Universal_Chat.py")

# System Status (Minimal)
st.divider()
with st.expander("🔌 System Status"):
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            response = requests.get(f"{BASE_URL}/host/v1/health", timeout=2)
            if response.ok:
                st.success("✅ Backend Service: **Connected**")
                health_data = response.json()
                if health_data.get("status") == "UP":
                    st.caption("All systems operational")
            else:
                st.error("⚠️ Backend Service: **Unhealthy**")
                st.caption("Service is running but reporting issues")
        except requests.exceptions.RequestException:
            st.error("❌ Backend Service: **Not Available**")
            st.caption("Please start the Agents-MCP-Host Java service on port 8080")
    
    with col2:
        st.info("""
        **Quick Check:**
        - Backend should be running on port 8080
        - Database connections configured
        - MCP servers initialized
        """)

# Footer
st.divider()
st.caption("""
**About This System**: Built on the MCP (Model Context Protocol) architecture with intelligent milestone-based processing. 
Each milestone represents a discrete step in understanding and answering your data questions.
""")