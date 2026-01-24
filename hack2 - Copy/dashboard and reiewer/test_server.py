#!/usr/bin/env python
"""Simple test server to verify code review works"""

import json
import sys
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Test that imports work
try:
    from app.services.review_service import CodeReviewService
    print("✓ Review service imported successfully")
except Exception as e:
    print(f"✗ Failed to import review service: {e}")
    traceback.print_exc()
    sys.exit(1)

# Create app
app = FastAPI(title="AI PR Reviewer Test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Test Server Running",
        "version": "1.0.0",
        "test_endpoint": "/test-review"
    }

@app.post("/test-review")
async def test_review():
    """Test the review service"""
    try:
        service = CodeReviewService()
        print("✓ Review service instantiated")
        
        result = service.review_code(
            code="def hello():\n    pass",
            language="python",
            context="test"
        )
        print("✓ Code review completed")
        return result
    except Exception as e:
        print(f"✗ Review failed: {e}")
        traceback.print_exc()
        return {"error": str(e), "traceback": traceback.format_exc()}

if __name__ == "__main__":
    import uvicorn
    print("Starting test server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
