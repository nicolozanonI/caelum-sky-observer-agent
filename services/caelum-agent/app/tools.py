"""
Tool functions for the caelum-agent microservice.
These tools call other microservices to get data.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import json
import pytz
import requests


# Service URLs (can be configured via environment variables)
SKYFIELD_URL = os.getenv("SKYFIELD_URL", "http://caelum-skyfield:8001")
GRAPH_URL = os.getenv("GRAPH_URL", "http://caelum-graph:8002")

# Timeout for service calls
SERVICE_TIMEOUT = 30


def call_skyfield_service(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Call the skyfield microservice."""
    url = f"{SKYFIELD_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=SERVICE_TIMEOUT)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=SERVICE_TIMEOUT)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Skyfield service error: {str(e)}"}


def call_graph_service(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Call the graph microservice."""
    url = f"{GRAPH_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=SERVICE_TIMEOUT)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=SERVICE_TIMEOUT)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Graph service error: {str(e)}"}


# ---------------------------------------------------------------------------
# Tool 1: Get Visible Sky Pills
# ---------------------------------------------------------------------------

def get_visible_sky_pills(
    latitude: float,
    longitude: float,
    timestamp: Optional[Union[datetime, str]] = None,
    include_planets: bool = True,
    include_stars: bool = True,
    include_deep_sky: bool = True,
    include_constellations: bool = False
) -> Dict[str, Any]:
    """
    Tool function: Calculate visible celestial bodies for a given observer location.
    
    Calls the caelum-skyfield microservice.
    
    Args:
        latitude: Observer latitude in degrees (-90 to 90)
        longitude: Observer longitude in degrees (-180 to 180)
        timestamp: Optional UTC datetime (string or datetime object)
        include_planets: Include planets and Moon
        include_stars: Include stars
        include_deep_sky: Include deep sky objects
        include_constellations: Include constellations
    
    Returns:
        Dictionary with visible objects, observer info, and metadata
    
    Note: Only returns objects above the horizon (altitude > 0 degrees).
    Note: Strictly excludes artificial satellites - natural bodies only.
    """
    # Convert timestamp to string if it's a datetime
    timestamp_str = None
    if timestamp is not None:
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.isoformat()
        else:
            timestamp_str = str(timestamp)
    
    # Prepare request data
    data = {
        "latitude": latitude,
        "longitude": longitude,
        "include_planets": include_planets,
        "include_stars": include_stars,
        "include_deep_sky": include_deep_sky,
        "include_constellations": include_constellations
    }
    
    if timestamp_str:
        data["timestamp"] = timestamp_str
    
    # Call skyfield service
    result = call_skyfield_service("/calculate", "POST", data=data)
    
    if "error" in result:
        return {"error": result["error"]}
    
    # Extract and transform the data
    if result.get("success"):
        sky_data = result.get("data", {})
        
        # Transform to pills format
        visible_objects = []
        for obj in sky_data.get('visible_objects', []):
            visible_objects.append({
                'name': obj.get('object'),
                'type': obj.get('type'),
                'category': obj.get('category'),
                'altitude': obj.get('altitude_degrees'),
                'azimuth': obj.get('azimuth_degrees'),
                'magnitude': obj.get('magnitude'),
                'visible': obj.get('visible', True),
                'distance_au': obj.get('distance_au'),
                'distance_light_years': obj.get('distance_light_years'),
                'constellation': obj.get('constellation'),
                'messier': obj.get('messier'),
                'abbreviation': obj.get('abbreviation')
            })
        
        return {
            'visible_objects': visible_objects,
            'observer': sky_data.get('observer', {}),
            'metadata': {
                'total_count': sky_data.get('visible_count', 0),
                'timestamp_utc': sky_data.get('observer', {}).get('time_utc'),
                'calculated_at': datetime.now(pytz.utc).isoformat()
            }
        }
    
    return {"error": "Invalid response from skyfield service"}


# ---------------------------------------------------------------------------
# Tool 2: Get Celestial History
# ---------------------------------------------------------------------------

def get_celestial_history(
    celestial_body: str,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Tool function: Retrieve human exploration history for a celestial body.
    
    Calls the caelum-graph microservice.
    
    Args:
        celestial_body: Name of the celestial body
        limit: Optional limit on number of results
    
    Returns:
        Dictionary with body info, missions, spacecraft, events, organizations
    """
    # Call graph service
    result = call_graph_service(f"/context/{celestial_body}", "GET")
    
    if "error" in result:
        return {
            'body': {'name': celestial_body},
            'missions': [],
            'spacecraft': [],
            'events': [],
            'organizations': []
        }
    
    if result.get("success"):
        data = result.get("data", {})
        
        # Ensure all fields are present
        return {
            'body': data.get('body', {'name': celestial_body}),
            'missions': data.get('missions', []),
            'spacecraft': data.get('spacecraft', []),
            'events': data.get('events', []),
            'organizations': data.get('organizations', [])
        }
    
    return {
        'body': {'name': celestial_body},
        'missions': [],
        'spacecraft': [],
        'events': [],
        'organizations': []
    }


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------

TOOL_REGISTRY = {
    'get_visible_sky_pills': {
        'name': 'get_visible_sky_pills',
        'description': 'Calculate visible celestial bodies for a given observer location. Returns planets, stars, deep sky objects, and constellations that are above the horizon. Strictly excludes artificial satellites.',
        'parameters': {
            'type': 'object',
            'properties': {
                'latitude': {
                    'type': 'number',
                    'description': 'Observer latitude in degrees (-90 to 90)',
                    'minimum': -90.0,
                    'maximum': 90.0
                },
                'longitude': {
                    'type': 'number',
                    'description': 'Observer longitude in degrees (-180 to 180)',
                    'minimum': -180.0,
                    'maximum': 180.0
                },
                'timestamp': {
                    'type': 'string',
                    'description': 'Optional UTC timestamp for observation (ISO format)',
                    'format': 'date-time'
                },
                'include_planets': {
                    'type': 'boolean',
                    'description': 'Include planets and Moon',
                    'default': True
                },
                'include_stars': {
                    'type': 'boolean',
                    'description': 'Include stars',
                    'default': True
                },
                'include_deep_sky': {
                    'type': 'boolean',
                    'description': 'Include deep sky objects',
                    'default': True
                },
                'include_constellations': {
                    'type': 'boolean',
                    'description': 'Include constellations',
                    'default': False
                }
            },
            'required': ['latitude', 'longitude']
        }
    },
    'get_celestial_history': {
        'name': 'get_celestial_history',
        'description': 'Retrieve human exploration history for a celestial body. Returns missions, spacecraft, events, and organizations related to exploration of the specified natural celestial body.',
        'parameters': {
            'type': 'object',
            'properties': {
                'celestial_body': {
                    'type': 'string',
                    'description': 'Name of the celestial body',
                    'enum': ['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 
                             'Moon', 'Sun', 'Sirius', 'Betelgeuse', 'Vega', 'Polaris', 'Arcturus',
                             'Andromeda Galaxy', 'Orion Nebula', 'Pleiades', 'Orion', 'Ursa Major', 'Cassiopeia']
                },
                'limit': {
                    'type': 'integer',
                    'description': 'Maximum number of results to return',
                    'minimum': 1,
                    'maximum': 100
                }
            },
            'required': ['celestial_body']
        }
    }
}


def get_tool_schema(tool_name: str) -> Dict[str, Any]:
    """Get the schema for a specific tool."""
    return TOOL_REGISTRY.get(tool_name, {})


def get_available_tools() -> List[Dict[str, Any]]:
    """Get a list of all available tools."""
    return list(TOOL_REGISTRY.values())


def call_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Call a tool by name with the given arguments."""
    tool_map = {
        'get_visible_sky_pills': get_visible_sky_pills,
        'get_celestial_history': get_celestial_history
    }
    
    if tool_name not in tool_map:
        return {
            'error': f'Tool {tool_name} not found',
            'available_tools': list(TOOL_REGISTRY.keys())
        }
    
    try:
        result = tool_map[tool_name](**arguments)
        return {
            'result': result,
            'tool_name': tool_name,
            'status': 'success'
        }
    except Exception as e:
        return {
            'error': str(e),
            'tool_name': tool_name,
            'status': 'error'
        }
