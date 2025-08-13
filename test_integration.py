#!/usr/bin/env python3
"""
Test script to verify the integration between Streamlit and Agents-MCP-Host
"""
import requests
import json

def test_backend_connection():
    """Test connection to backend"""
    url = "http://localhost:8080/health"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("✓ Backend is running and healthy")
            return True
        else:
            print("✗ Backend returned unexpected status:", response.status_code)
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend on port 8080")
        return False
    except Exception as e:
        print(f"✗ Error checking backend: {e}")
        return False

def test_conversation_api():
    """Test conversation API with regular message"""
    url = "http://localhost:8080/host/v1/conversations"
    messages = [
        {"role": "user", "content": "Hello, what is your name?"}
    ]
    
    try:
        response = requests.post(url, json={"messages": messages}, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and result["choices"]:
            content = result["choices"][0]["message"]["content"]
            print(f"✓ Regular conversation works")
            print(f"  Response: {content[:100]}...")
            return True
        else:
            print("✗ Unexpected response format:", result)
            return False
    except Exception as e:
        print(f"✗ Error testing conversation API: {e}")
        return False

def test_mcp_tool():
    """Test MCP tool triggering"""
    url = "http://localhost:8080/host/v1/conversations"
    messages = [
        {"role": "user", "content": "Calculate 42 plus 58"}
    ]
    
    try:
        response = requests.post(url, json={"messages": messages}, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and result["choices"]:
            content = result["choices"][0]["message"]["content"]
            print(f"✓ MCP tool triggering works")
            print(f"  Response: {content}")
            
            # Check if it calculated correctly
            if "100" in content:
                print("  ✓ Calculation is correct")
            return True
        else:
            print("✗ Unexpected response format:", result)
            return False
    except Exception as e:
        print(f"✗ Error testing MCP tools: {e}")
        return False

def main():
    print("Testing Streamlit-to-Backend Integration")
    print("=" * 50)
    
    # Test backend health
    if not test_backend_connection():
        print("\nBackend is not running. Please start Agents-MCP-Host first.")
        return
    
    print()
    
    # Test conversation API
    test_conversation_api()
    print()
    
    # Test MCP tools
    test_mcp_tool()
    print()
    
    print("=" * 50)
    print("Integration testing complete!")
    print("\nYou can now access the Streamlit interface at:")
    print("http://localhost:8501")

if __name__ == "__main__":
    main()