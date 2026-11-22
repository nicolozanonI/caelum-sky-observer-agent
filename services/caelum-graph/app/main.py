"""
Main FastAPI application for caelum-graph microservice.
Provides knowledge graph API for human space exploration history.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.service import graph_service

# Create FastAPI app
app = FastAPI(
    title="Caelum Graph Service",
    description="Microservice for querying human space exploration history from Neo4j knowledge graph.",
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


# Models
class QueryRequest(BaseModel):
    """Request model for custom queries."""
    cypher: str = Field(..., description="Cypher query to execute")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")


class SeedRequest(BaseModel):
    """Request model for seeding the graph."""
    force: bool = Field(False, description="Force re-seed even if already seeded")


# Endpoints
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "service": "caelum-graph",
        "version": "1.0.0",
        "description": "Knowledge graph microservice",
        "docs": "/docs"
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    neo4j_healthy = graph_service.verify_connection()
    return {
        "status": "healthy" if neo4j_healthy else "unhealthy",
        "service": "caelum-graph",
        "neo4j": neo4j_healthy,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/seed", tags=["Data"], summary="Seed the knowledge graph")
async def seed_graph(request: Optional[SeedRequest] = None):
    """
    Seed the Neo4j knowledge graph with basic space exploration data.
    
    Creates nodes for organizations, missions, spacecraft, celestial bodies, and events.
    """
    try:
        result = graph_service.seed_basic_subgraph()
        return {
            "success": result.get("status") == "success",
            "data": result,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error seeding graph: {str(e)}"
        )


@app.get("/context/{celestial_body}", tags=["Queries"], summary="Get exploration context")
async def get_context(celestial_body: str):
    """
    Get human exploration history for a specific celestial body.
    
    Returns missions, spacecraft, events, and organizations related to the body.
    """
    try:
        result = graph_service.get_exploration_context(celestial_body)
        
        if result.get("status") == "not_found":
            return {
                "success": True,
                "celestial_body": celestial_body,
                "message": result.get("message", ""),
                "data": {
                    "body": result.get("body", {}),
                    "missions": result.get("missions", []),
                    "spacecraft": result.get("spacecraft", []),
                    "events": result.get("events", []),
                    "organizations": result.get("organizations", [])
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        if result.get("status") == "success":
            context = result.get("context", {})
            return {
                "success": True,
                "celestial_body": celestial_body,
                "data": context,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        return {
            "success": False,
            "error": result.get("message", "Unknown error"),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting context: {str(e)}"
        )


@app.get("/missions/{celestial_body}", tags=["Queries"], summary="Get mission history")
async def get_missions(celestial_body: str, limit: int = Query(50, ge=1, le=100)):
    """
    Get chronological mission history for a specific celestial body.
    """
    try:
        result = graph_service.get_mission_history(celestial_body, limit=limit)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Unknown error"))
        
        return {
            "success": True,
            "celestial_body": celestial_body,
            "missions": result.get("missions", []),
            "count": result.get("count", 0),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting missions: {str(e)}"
        )


@app.post("/query", tags=["Queries"], summary="Execute custom Cypher query")
async def execute_query(request: QueryRequest):
    """
    Execute a custom Cypher query against the knowledge graph.
    
    **Warning:** This endpoint allows arbitrary Cypher queries. Use with caution.
    """
    try:
        result = graph_service.query(request.cypher, request.parameters)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Query error"))
        
        return {
            "success": True,
            "records": result.get("records", []),
            "count": result.get("count", 0),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing query: {str(e)}"
        )


@app.get("/bodies", tags=["Data"], summary="Get all celestial bodies")
async def get_celestial_bodies():
    """Get a list of all celestial bodies in the knowledge graph."""
    try:
        bodies = graph_service.get_all_celestial_bodies()
        return {
            "success": True,
            "bodies": bodies,
            "count": len(bodies),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting celestial bodies: {str(e)}"
        )


@app.get("/missions", tags=["Data"], summary="Get all missions")
async def get_all_missions():
    """Get a list of all missions in the knowledge graph."""
    try:
        missions = graph_service.get_all_missions()
        return {
            "success": True,
            "missions": missions,
            "count": len(missions),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting missions: {str(e)}"
        )
