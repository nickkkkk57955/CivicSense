#!/usr/bin/env python3
"""
Startup script for the Civic Issue Reporting System
"""
import uvicorn
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main function to start the application"""
    print("Starting Civic Issue Reporting System...")
    print("API Documentation will be available at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    
    # Initialize database with sample data
    try:
        from app.init_db import create_sample_data
        create_sample_data()
    except Exception as e:
        print(f"Warning: Could not initialize sample data: {e}")
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
