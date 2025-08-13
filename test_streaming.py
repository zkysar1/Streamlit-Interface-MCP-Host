#!/usr/bin/env python3
"""
Test script to verify SSE streaming functionality
"""
import requests
from sseclient import SSEClient
import json

def test_streaming():
    """Test SSE streaming with tool call"""
    url = "http://localhost:8080/host/v1/conversations"
    headers = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"role": "user", "content": "Calculate 123 plus 456"}
        ]
    }
    
    print("Testing SSE streaming with calculator tool...")
    print("=" * 50)
    
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        
        client = SSEClient(response)
        
        for event in client.events():
            print(f"Event: {event.event}")
            if event.data:
                data = json.loads(event.data)
                print(f"Data: {json.dumps(data, indent=2)}")
            print("-" * 30)
            
            if event.event == 'done' or event.event == 'error':
                break
                
        print("\n✓ Streaming test completed successfully!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True

def test_regular_conversation():
    """Test SSE streaming with regular conversation"""
    url = "http://localhost:8080/host/v1/conversations"
    headers = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"role": "user", "content": "Hello, what is Python?"}
        ]
    }
    
    print("\n\nTesting SSE streaming with regular conversation...")
    print("=" * 50)
    
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        
        client = SSEClient(response)
        
        for event in client.events():
            print(f"Event: {event.event}")
            if event.data:
                data = json.loads(event.data)
                # Truncate long content for display
                if 'content' in data and len(data['content']) > 100:
                    data['content'] = data['content'][:100] + "..."
                print(f"Data: {json.dumps(data, indent=2)}")
            print("-" * 30)
            
            if event.event == 'done' or event.event == 'error':
                break
                
        print("\n✓ Regular conversation test completed successfully!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("SSE Streaming Test Suite")
    print("=" * 50)
    
    # Test backend connectivity
    try:
        health = requests.get("http://localhost:8080/health", timeout=2)
        if health.status_code == 200:
            print("✓ Backend is running")
        else:
            print("✗ Backend returned unexpected status")
            exit(1)
    except:
        print("✗ Backend is not running. Please start Agents-MCP-Host first.")
        exit(1)
    
    # Run tests
    success = test_streaming()
    if success:
        test_regular_conversation()
    
    print("\n" + "=" * 50)
    print("All tests complete!")
    print("\nYou can now test the Streamlit interface at:")
    print("http://localhost:8501")