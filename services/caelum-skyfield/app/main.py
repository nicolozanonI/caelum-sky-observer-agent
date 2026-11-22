"""
Main FastAPI application for caelum-skyfield microservice.
Provides astronomical calculation API.
"""

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.engine import sky_engine

import traceback
import logging

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Caelum Skyfield Service",
    description="Microservice for astronomical position calculations using Skyfield and JPL ephemeris.",
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
class SkyRequest(BaseModel):
    """Request model for sky calculations."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Observer latitude in degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Observer longitude in degrees")
    timestamp: Optional[str] = Field(None, description="UTC timestamp (ISO format)")
    include_planets: bool = Field(True, description="Include planets")
    include_stars: bool = Field(True, description="Include stars")
    include_deep_sky: bool = Field(True, description="Include deep sky objects")
    include_constellations: bool = Field(False, description="Include constellations")


class ObjectPositionRequest(BaseModel):
    """Request model for object position."""
    object_name: str = Field(..., description="Name of the celestial object")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Observer latitude in degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Observer longitude in degrees")
    timestamp: Optional[str] = Field(None, description="UTC timestamp (ISO format)")


# Endpoints
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "service": "caelum-skyfield",
        "version": "1.0.0",
        "description": "Astronomical calculation microservice",
        "docs": "/docs"
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "caelum-skyfield",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/calculate", tags=["Calculations"], summary="Calculate visible sky")
async def calculate_sky(request: SkyRequest):
    """
    Calculate visible celestial bodies for a given observer location.
    
    **Note:** Strictly excludes artificial satellites - natural bodies only.
    """
    try:
        # Parse timestamp if provided
        timestamp = None
        if request.timestamp:
            try:
                timestamp = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        result = sky_engine.calculate_sky(
            latitude=request.latitude,
            longitude=request.longitude,
            target_time=timestamp,
            include_planets=request.include_planets,
            include_stars=request.include_stars,
            include_deep_sky=request.include_deep_sky,
            include_constellations=request.include_constellations
        )
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating sky: {str(e)}"
        )


@app.get("/calculate", tags=["Calculations"], summary="Calculate visible sky (GET)")
async def calculate_sky_get(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Observer latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Observer longitude"),
    timestamp: Optional[str] = Query(None, description="UTC timestamp (ISO format)"),
    include_planets: bool = Query(True, description="Include planets"),
    include_stars: bool = Query(True, description="Include stars"),
    include_deep_sky: bool = Query(True, description="Include deep sky objects"),
    include_constellations: bool = Query(False, description="Include constellations")
):
    """Calculate visible sky using GET parameters."""
    try:
        timestamp_obj = None
        if timestamp:
            try:
                timestamp_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        result = sky_engine.calculate_sky(
            latitude=lat,
            longitude=lon,
            target_time=timestamp_obj,
            include_planets=include_planets,
            include_stars=include_stars,
            include_deep_sky=include_deep_sky,
            include_constellations=include_constellations
        )
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"CRITICAL ERROR IN /calculate:\n{error_trace}")

        # Return the error in the HTTP response as well for convenience
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)} | Trace: {error_trace}"
        )


@app.post("/position/{object_name}", tags=["Calculations"], summary="Get object position")
async def get_object_position(
    object_name: str,
    request: ObjectPositionRequest
):
    """Get position of a specific celestial object."""
    try:
        timestamp_obj = None
        if request.timestamp:
            try:
                timestamp_obj = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
            except ValueError:
                pass

        result = sky_engine.get_object_position(
            object_name=object_name,
            latitude=request.latitude,
            longitude=request.longitude,
            target_time=timestamp_obj
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting object position: {str(e)}"
        )


@app.get("/catalog", tags=["Data"], summary="Get celestial catalog")
async def get_catalog():
    """Get the celestial catalog."""
    try:
        return {
            "success": True,
            "data": sky_engine.catalog,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting catalog: {str(e)}"
        )


@app.get("/catalog/planets", tags=["Data"], summary="Get planets catalog")
async def get_planets():
    """Get planets from the catalog."""
    return {
        "success": True,
        "data": sky_engine.catalog.get("planets", []),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/catalog/stars", tags=["Data"], summary="Get stars catalog")
async def get_stars():
    """Get stars from the catalog."""
    return {
        "success": True,
        "data": sky_engine.catalog.get("stars", []),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/catalog/deep_sky", tags=["Data"], summary="Get deep sky objects catalog")
async def get_deep_sky():
    """Get deep sky objects from the catalog."""
    return {
        "success": True,
        "data": sky_engine.catalog.get("deep_sky", []),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/catalog/constellations", tags=["Data"], summary="Get constellations catalog")
async def get_constellations():
    """Get constellations from the catalog."""
    return {
        "success": True,
        "data": sky_engine.catalog.get("constellations", []),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }