#!/usr/bin/env python3
"""
Minimal test to check what's happening
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Starting minimal test...")

try:
    print("1. Importing FastAPI...")
    from fastapi import FastAPI
    print("   ✓ FastAPI imported")
    
    print("2. Creating simple app...")
    app = FastAPI()
    
    @app.get("/")
    def read_root():
        return {"message": "Hello World"}
    
    @app.get("/test")
    def test():
        return {"message": "Test endpoint"}
    
    print("   ✓ Simple app created")
    
    print("3. Testing with TestClient...")
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    print("4. Testing root endpoint...")
    response = client.get("/")
    print(f"   Status: {response.status_code}")
    print(f"   Content: {response.text}")
    
    print("5. Testing test endpoint...")
    response = client.get("/test")
    print(f"   Status: {response.status_code}")
    print(f"   Content: {response.text}")
    
    print("✓ All tests passed!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
