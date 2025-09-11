import streamlit as st

# Page configuration
st.set_page_config(
    page_title="SQL Query Assistant",
    page_icon="🎯",
    layout="wide"
)

st.title("SQL Query Assistant")

st.markdown("""
This system transforms natural language questions into database insights through an intelligent 6-step pipeline. Each step builds on the previous one to progressively understand and answer your data questions.

## The 6-Step Pipeline

### Step 1: Intent Extraction
The system analyzes your question to understand what you're really asking. It identifies the type of data you need, the operations required, and how the results should be presented.

### Step 2: Schema Exploration  
The system explores the database schema to find relevant tables and relationships. It identifies which tables contain the data needed to answer your question.

### Step 3: Data Analysis
The system examines table columns, data types, and statistics. It analyzes the structure and content patterns to understand how to work with your data.

### Step 4: SQL Generation
Based on all gathered information, the system generates a precise, optimized SQL statement. This query is crafted to efficiently retrieve exactly what you need.

### Step 5: Query Execution
The generated SQL query is executed against the database. The system retrieves the actual data results from your database.

### Step 6: Natural Response
The raw query results are transformed into a clear, natural language answer. The system formats the data to directly address your original question.

## How Backstory and Guidance Work

The system uses two key concepts to control how it processes your questions:

### Backstory
The backstory defines your assistant's personality, expertise, and role. It determines how deeply the assistant will process through the pipeline. For example:
- A data analyst backstory will execute the full pipeline to provide data-driven answers
- A SQL developer backstory might stop at SQL generation without execution
- A schema explorer backstory could stop after discovering relevant tables

### Guidance
Guidance provides behavioral rules and constraints for the assistant. It sets specific boundaries on what the assistant should or shouldn't do. For example:
- "Always execute queries and provide results" ensures full pipeline execution
- "Generate SQL only, don't execute" stops at the SQL generation step
- "Focus on schema discovery" limits processing to early pipeline stages

Together, backstory and guidance intelligently control which pipeline steps are executed for each query, ensuring you get exactly the type of response you need.

## Available Prebuilt Agents

The Universal Chat page provides four prebuilt agent configurations:

### Oracle DB Answerer
This agent is a senior database analyst with deep Oracle expertise. It executes the full pipeline to provide data-driven answers by actually querying your database. It explores schemas, generates SQL, executes queries, and formats results into clear answers. Use this when you need actual data insights.

### Oracle SQL Builder
This agent specializes in SQL generation and optimization. It processes through the pipeline up to SQL generation but doesn't execute queries. It provides detailed explanations of the SQL it generates, including optimization strategies. Use this when you need SQL statements without running them.

### Direct LLM No Tool
This agent operates without any database access or tools. It uses only general knowledge to answer questions. It cannot execute queries or access your database. Use this for general database concepts or when you want advice without touching your data.

### Free Agent
This agent allows you to define your own custom backstory and guidance. You provide the personality and rules, giving you complete control over how the assistant behaves and which pipeline steps it executes. Use this for specialized scenarios that don't fit the other prebuilt agents.

## Getting Started

Navigate to the Universal Chat page to start asking questions. Select an agent that matches your needs, or create your own with the Free Agent option. The system will automatically determine which pipeline steps to execute based on your chosen agent and the nature of your question.
""")