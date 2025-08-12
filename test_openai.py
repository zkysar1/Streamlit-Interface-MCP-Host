#!/usr/bin/env python3
"""
Test script to verify OpenAI API integration
"""
import os
import sys

# Check if openai module is available
try:
    from openai import OpenAI
    print("✓ OpenAI module imported successfully")
except ImportError:
    print("✗ OpenAI module not found. Please install: pip install openai")
    sys.exit(1)

# Check environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("✗ OPENAI_API_KEY environment variable not set")
    sys.exit(1)
else:
    print("✓ OPENAI_API_KEY environment variable is set")

# Test API connection
try:
    client = OpenAI(api_key=api_key)
    print("✓ OpenAI client initialized")
    
    # Test a simple completion
    print("\nTesting API call with gpt-4o-mini-2024-07-18...")
    completion = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, World!' in exactly 2 words."}
        ],
        max_tokens=10,
        temperature=0.2
    )
    
    response = completion.choices[0].message.content
    print(f"✓ API Response: {response}")
    print("\nAll tests passed! The OpenAI integration is working correctly.")
    
except Exception as e:
    print(f"✗ Error testing API: {e}")
    sys.exit(1)