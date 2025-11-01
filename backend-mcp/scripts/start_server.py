#!/usr/bin/env python3
"""
TravelMate AI - Start FastAPI Server
Quick start script for development
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from app.config import get_settings

settings = get_settings()

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 Starting TravelMate AI FastAPI Server")
    print("=" * 80)
    print(f"\n📡 API Server: http://0.0.0.0:{settings.api_port}")
    print(f"📚 API Docs: http://localhost:{settings.api_port}/docs")
    print(f"🔧 Environment: {settings.environment}")
    print("\n" + "=" * 80 + "\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )

