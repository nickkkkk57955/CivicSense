#!/usr/bin/env python3
"""
Test script to check the FastAPI app
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import app
    print("App imported successfully")
    print("App routes:")
    for route in app.routes:
        print(f"  {route.path} - {route.methods if hasattr(route, 'methods') else 'N/A'}")
    
    # Test the root endpoint
    print("\nTesting root endpoint...")
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/")
    print(f"Root endpoint response: {response.status_code}")
    print(f"Content: {response.text}")
    
    # Test the test endpoint
    print("\nTesting /test endpoint...")
    response = client.get("/test")
    print(f"Test endpoint response: {response.status_code}")
    print(f"Content: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
