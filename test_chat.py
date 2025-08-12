#!/usr/bin/env python3
"""
Test the chat functionality directly
"""
import os
from openai import OpenAI

# Check environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("✗ OPENAI_API_KEY environment variable not set")
    exit(1)

print("Testing chat functionality...")
client = OpenAI(api_key=api_key)

# Simulate the chat conversation
messages = [
    {"role": "system", "content": "Be helpful and truthful."},
    {"role": "user", "content": "What is 2+2?"}
]

try:
    completion = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=messages,
        max_tokens=400,
        temperature=0.2
    )
    
    response = completion.choices[0].message.content
    print(f"\n✓ Chat test successful!")
    print(f"User: What is 2+2?")
    print(f"Assistant: {response}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)