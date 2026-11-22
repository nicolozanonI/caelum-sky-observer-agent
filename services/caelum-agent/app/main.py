"""
Main FastAPI application for caelum-agent microservice.
Secure version: NO free text input. Only structured requests.
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing_extensions import Literal

from app.agent import caelum_agent, CaelumAgent, create_agent
from app.tools import get_visible_sky_pills, get_celestial_history, get_available_tools


# Create FastAPI app
app = FastAPI(
    title="Caelum Agent Service",
    description="Secure microservice for structured astronomical queries. "
                "NO free text input allowed. Uses LangChain + LangGraph + Google Gemini INTERNALLY.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Models (Structured Input ONLY - NO free text)
# ============================================================================

class StructuredQueryRequest(BaseModel):
    """
    Secure request model: ONLY structured parameters, NO free text.
    """
    action: Literal["get_visible_objects", "get_object_details", "get_object_history"] = Field(
        ...,
        description="Predefined action: get_visible_objects, get_object_details, or get_object_history"
    )
    latitude: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Observer latitude in degrees (required for location-based actions)"
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Observer longitude in degrees (required for location-based actions)"
    )
    object_name: Optional[str] = Field(
        None,
        description="Celestial body name (required for get_object_details and get_object_history)"
    )
    timestamp: Optional[str] = Field(
        None,
        description="UTC timestamp for sky calculations (ISO format)"
    )
    include_planets: bool = Field(
        True,
        description="Include planets in visible objects"
    )
    include_stars: bool = Field(
        True,
        description="Include stars in visible objects"
    )
    include_deep_sky: bool = Field(
        True,
        description="Include deep sky objects in visible objects"
    )


# ============================================================================
# Root and Health Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "service": "caelum-agent",
        "version": "1.0.0",
        "description": "Secure microservice for structured astronomical queries. "
                      "Uses LangChain + LangGraph + Google Gemini INTERNALLY for narration.",
        "docs": "/docs",
        "note": "NO free text input allowed. Use /api/v1/agent/structured endpoint with structured parameters."
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "caelum-agent",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# ============================================================================
# Secure Endpoints (NO free text input)
# ============================================================================

@app.post("/api/v1/agent/structured", tags=["Agent"], 
          summary="Structured query endpoint - NO free text input")
async def structured_query(request: StructuredQueryRequest):
    """
    SECURE endpoint: accepts ONLY structured parameters, NO free text.
    
    The agent uses LangChain + LangGraph + Google Gemini INTERNALLY to:
    1. Call the appropriate tools (skyfield and/or graph services)
    2. Generate a human-readable narration
    
    **Important**: This endpoint does NOT accept free text messages.
    Use predefined actions: get_visible_objects, get_object_details, get_object_history
    """
    try:
        result = caelum_agent.process_structured(
            action=request.action,
            latitude=request.latitude,
            longitude=request.longitude,
            object_name=request.object_name,
            timestamp=request.timestamp,
            include_planets=request.include_planets,
            include_stars=request.include_stars,
            include_deep_sky=request.include_deep_sky
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing structured query: {str(e)}"
        )


# ============================================================================
# Utility Endpoints (for internal use)
# ============================================================================

@app.get("/api/v1/tools", tags=["Tools"], summary="List available tools")
async def list_tools():
    """List all available tools that the agent can use internally."""
    tools = get_available_tools()
    return {
        "tools": tools,
        "count": len(tools),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
