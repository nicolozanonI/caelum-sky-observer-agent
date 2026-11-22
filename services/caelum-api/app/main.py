"""
Main FastAPI application for caelum-api gateway microservice.
Single entry point that routes requests to appropriate microservices.
Secure version: NO free text chat endpoints.
"""

import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import requests


# Service URLs (can be configured via environment variables)
SKYFIELD_URL = os.getenv("SKYFIELD_URL", "http://caelum-skyfield:8001")
GRAPH_URL = os.getenv("GRAPH_URL", "http://caelum-graph:8002")
AGENT_URL = os.getenv("AGENT_URL", "http://caelum-agent:8003")

# Timeout for service calls
SERVICE_TIMEOUT = 30

# Create FastAPI app
app = FastAPI(
    title="Caelum API Gateway",
    description="Single entry point for all Caelum microservices. "
                "NO free text input allowed. All endpoints use structured parameters only.",
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
# Helper Function for Request Forwarding
# ============================================================================

from fastapi.responses import JSONResponse


def forward_request(
        url: str,
        method: str = "GET",
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None
):
    """Forward a request to another service and return parsed JSON."""
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, headers=headers, timeout=SERVICE_TIMEOUT)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=SERVICE_TIMEOUT)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=SERVICE_TIMEOUT)
        elif method.upper() == "DELETE":
            response = requests.delete(url, json=data, headers=headers, timeout=SERVICE_TIMEOUT)
        else:
            raise HTTPException(status_code=405, detail="Method not allowed")

        response.raise_for_status()
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Service unavailable: {str(e)}"
        )


# ============================================================================
# Health and Info Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "name": "Caelum API Gateway",
        "version": "1.0.0",
        "description": "Single entry point for Caelum microservices",
        "services": {
            "skyfield": f"{SKYFIELD_URL}",
            "graph": f"{GRAPH_URL}",
            "agent": f"{AGENT_URL}"
        },
        "docs": "/docs",
        "note": "NO free text input allowed. Use structured endpoints only."
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Health check for all services."""
    services_health = {}
    
    # Check Skyfield service
    try:
        response = requests.get(f"{SKYFIELD_URL}/health", timeout=5)
        services_health["skyfield"] = response.status_code == 200
    except:
        services_health["skyfield"] = False
    
    # Check Graph service
    try:
        response = requests.get(f"{GRAPH_URL}/health", timeout=5)
        services_health["graph"] = response.status_code == 200
    except:
        services_health["graph"] = False
    
    # Check Agent service
    try:
        response = requests.get(f"{AGENT_URL}/health", timeout=5)
        services_health["agent"] = response.status_code == 200
    except:
        services_health["agent"] = False
    
    all_healthy = all(services_health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "gateway": "healthy",
        "services": services_health,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/info", tags=["System"])
async def get_info():
    """Get API gateway information."""
    return {
        "name": "Caelum API Gateway",
        "version": "1.0.0",
        "description": "Microservices architecture for astronomical observation backend",
        "architecture": "microservices",
        "services": {
            "caelum-skyfield": {
                "port": 8001,
                "description": "Astronomical calculations using Skyfield",
                "endpoints": [
                    "GET /calculate",
                    "POST /calculate",
                    "POST /position/{object}",
                    "GET /catalog",
                    "GET /catalog/planets",
                    "GET /catalog/stars",
                    "GET /catalog/deep_sky",
                    "GET /catalog/constellations"
                ]
            },
            "caelum-graph": {
                "port": 8002,
                "description": "Knowledge graph for space exploration history",
                "endpoints": [
                    "POST /seed",
                    "GET /context/{body}",
                    "GET /missions/{body}",
                    "POST /query",
                    "GET /bodies",
                    "GET /missions"
                ]
            },
            "caelum-agent": {
                "port": 8003,
                "description": "Secure agent with structured input (NO free text)",
                "endpoints": [
                    "POST /api/v1/agent/structured (NO free text input)"
                ]
            }
        },
        "core_constraints": {
            "natural_bodies_only": True,
            "no_artificial_satellites": True,
            "visibility_guardrail": True,
            "no_free_text_input": True  # NEW
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# ============================================================================
# Agent Endpoints (Structured Input ONLY - NO free text)
# ============================================================================

class StructuredAgentRequest(BaseModel):
    """
    Structured request model for agent queries.
    NO free text input allowed - only predefined actions and parameters.
    """
    action: str = Field(..., description="Action: get_visible_objects, get_object_details, get_object_history")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Observer latitude")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Observer longitude")
    object_name: Optional[str] = Field(None, description="Celestial body name (required for object actions)")
    timestamp: Optional[str] = Field(None, description="UTC timestamp (ISO format)")
    include_planets: bool = Field(True, description="Include planets")
    include_stars: bool = Field(True, description="Include stars")
    include_deep_sky: bool = Field(True, description="Include deep sky objects")




@app.post("/api/v1/sky/action", tags=["Agent"],
          summary="Structured agent query - NO free text input")
async def agent_action(request: StructuredAgentRequest):

    """
    SECURE endpoint: Forward structured request to caelum-agent.

    **Important**: This endpoint does NOT accept free text messages.
    Use predefined actions: get_visible_objects, get_object_details, get_object_history

    **Core Constraints:**
    - Natural celestial bodies only (no artificial satellites)
    - Visibility guardrail: historical context only for visible objects
    - NO free text input allowed
    """
    try:
        return forward_request(
            f"{AGENT_URL}/api/v1/agent/structured",
            "POST",
            data=request.model_dump()  # o request.dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error forwarding request: {str(e)}"
        )


# ============================================================================
# Skyfield Endpoints (Proxy to caelum-skyfield:8001)
# ============================================================================

@app.get("/api/v1/sky/view", tags=["Skyfield"], summary="Get visible celestial objects")
async def sky_view(request: Request):
    """Proxy request to caelum-skyfield /calculate endpoint (GET)."""
    params = dict(request.query_params)
    return forward_request(f"{SKYFIELD_URL}/calculate", "GET", params=params)


@app.post("/api/v1/sky/view", tags=["Skyfield"], summary="Get visible celestial objects (POST)")
async def sky_view_post(request: Request):
    """Proxy request to caelum-skyfield /calculate endpoint (POST)."""
    return forward_request(f"{SKYFIELD_URL}/calculate", "POST", await request.json())


@app.get("/api/v1/sky/catalog", tags=["Skyfield"], summary="Get celestial catalog")
async def sky_catalog():
    """Proxy request to caelum-skyfield /catalog endpoint."""
    return forward_request(f"{SKYFIELD_URL}/catalog", "GET")


@app.get("/api/v1/sky/catalog/planets", tags=["Skyfield"], summary="Get planets catalog")
async def sky_planets():
    """Proxy request to caelum-skyfield /catalog/planets endpoint."""
    return forward_request(f"{SKYFIELD_URL}/catalog/planets", "GET")


@app.get("/api/v1/sky/catalog/stars", tags=["Skyfield"], summary="Get stars catalog")
async def sky_stars():
    """Proxy request to caelum-skyfield /catalog/stars endpoint."""
    return forward_request(f"{SKYFIELD_URL}/catalog/stars", "GET")


@app.get("/api/v1/sky/catalog/deep_sky", tags=["Skyfield"], summary="Get deep sky objects catalog")
async def sky_deep_sky():
    """Proxy request to caelum-skyfield /catalog/deep_sky endpoint."""
    return forward_request(f"{SKYFIELD_URL}/catalog/deep_sky", "GET")


@app.get("/api/v1/sky/catalog/constellations", tags=["Skyfield"], summary="Get constellations catalog")
async def sky_constellations():
    """Proxy request to caelum-skyfield /catalog/constellations endpoint."""
    return forward_request(f"{SKYFIELD_URL}/catalog/constellations", "GET")


# ============================================================================
# Graph Endpoints (Proxy to caelum-graph:8002)
# ============================================================================

@app.post("/api/v1/sky/seed", tags=["Graph"], summary="Seed knowledge graph")
async def graph_seed(request: Request):
    """Proxy request to caelum-graph /seed endpoint."""
    return forward_request(f"{GRAPH_URL}/seed", "POST", await request.json())


@app.get("/api/v1/sky/context/{object_name}", tags=["Graph"], summary="Get exploration context")
async def graph_context(object_name: str):
    """Proxy request to caelum-graph /context/{object_name} endpoint."""
    return forward_request(f"{GRAPH_URL}/context/{object_name}", "GET")


@app.get("/api/v1/sky/missions/{object_name}", tags=["Graph"], summary="Get mission history")
async def graph_missions(object_name: str, limit: Optional[int] = None):
    """Proxy request to caelum-graph /missions/{object_name} endpoint."""
    params = {}
    if limit is not None:
        params['limit'] = limit
    return forward_request(f"{GRAPH_URL}/missions/{object_name}", "GET", params=params)


@app.post("/api/v1/sky/query", tags=["Graph"], summary="Execute custom Cypher query")
async def graph_query(request: Request):
    """Proxy request to caelum-graph /query endpoint."""
    return forward_request(f"{GRAPH_URL}/query", "POST", await request.json())


@app.get("/api/v1/sky/bodies", tags=["Graph"], summary="Get all celestial bodies")
async def graph_bodies():
    """Proxy request to caelum-graph /bodies endpoint."""
    return forward_request(f"{GRAPH_URL}/bodies", "GET")


@app.get("/api/v1/sky/missions", tags=["Graph"], summary="Get all missions")
async def graph_all_missions():
    """Proxy request to caelum-graph /missions endpoint."""
    return forward_request(f"{GRAPH_URL}/missions", "GET")


# ============================================================================
# Legacy Endpoints (for backward compatibility)
# ============================================================================

@app.post("/api/v1/sky-view", tags=["Legacy"], deprecated=True)
async def legacy_sky_view(request: Request):
    """Legacy endpoint - redirects to /api/v1/sky/view."""
    params = dict(request.query_params)
    return forward_request(f"{SKYFIELD_URL}/calculate", "GET", params=params)
