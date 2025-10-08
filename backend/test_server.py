"""
Simple test server to verify basic FastAPI setup
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

# Create FastAPI app
app = FastAPI(
    title="Healthcare AI Backend - Test",
    description="Simple test server",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple response model
class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {"message": "Healthcare AI Backend is running!"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Server is running successfully",
        version="1.0.0"
    )

@app.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {
        "success": True,
        "data": {
            "timestamp": "2024-01-01T00:00:00Z",
            "environment": "development",
            "features": ["basic", "health_check", "cors"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
