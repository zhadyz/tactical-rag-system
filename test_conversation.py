#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for conversation memory system
Simulates a multi-turn conversation to verify context tracking
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time

# Gradio API endpoint
API_URL = "http://localhost:7860/api/predict"

def query_rag(message, history=[]):
    """Send a query to the RAG system"""
    payload = {
        "data": [message, history]
    }

    response = requests.post(API_URL, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result.get("data", [None, ""])[1]
    else:
        return f"Error: {response.status_code}"

def main():
    print("=" * 70)
    print("CONVERSATION MEMORY TEST - Multi-Turn Interaction")
    print("=" * 70)
    print()

    # Conversation history for Gradio
    history = []

    # Test conversation - designed to test follow-up detection
    queries = [
        "What are the main protocols mentioned in these documents?",
        "Can you tell me more about those?",  # Follow-up - should use context
        "What specific requirements are there?",
        "How do they apply to personnel?",  # Follow-up
        "Are there any exceptions?",  # Follow-up
        "What about disciplinary actions?",  # Follow-up - this triggers summarization (5th exchange)
        "Can you summarize the key points we discussed?",  # Should use summarized context
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'-' * 70}")
        print(f"TURN {i}/7")
        print(f"{'-' * 70}")
        print(f"USER: {query}")
        print()

        # Add a small delay to be polite to the API
        if i > 1:
            time.sleep(2)

        # Send query
        response = query_rag(query, history)

        # Update history
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": response})

        # Print response (truncated for readability)
        print(f"ASSISTANT: {response[:500]}...")

        # Check if this was detected as a follow-up
        if any(indicator in query.lower() for indicator in ["those", "they", "them", "this", "that"]):
            print()
            print("✓ Expected follow-up question - context should be used")

        # Note when summarization should trigger
        if i == 5:
            print()
            print("⚠ SUMMARIZATION TRIGGER: This is the 5th exchange")
            print("   Conversation memory should compress history now")

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print()
    print("Conversation tested the following features:")
    print("  ✓ Initial query (no context)")
    print("  ✓ Follow-up questions with pronouns ('those', 'they', 'that')")
    print("  ✓ Sliding window (7 exchanges)")
    print("  ✓ Automatic summarization trigger (after 5th exchange)")
    print("  ✓ Using summarized context for subsequent questions")
    print()
    print("To verify conversation memory, check Docker logs:")
    print("  docker logs rag-tactical-system | grep -i 'conversation\\|follow\\|summar'")
    print()

if __name__ == "__main__":
    main()
