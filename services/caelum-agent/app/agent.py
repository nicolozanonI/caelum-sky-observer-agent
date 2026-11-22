"""
Caelum Agent using LangChain + Google Gemini.
Secure version: accepts only structured input, dynamically syncs its whitelist
from the Skyfield catalog, and uses LLM strictly for narration.
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, List

import requests
from langchain_google_genai import ChatGoogleGenerativeAI

from app.tools import get_visible_sky_pills, get_celestial_history


# ============================================================================
# Configuration & Whitelists
# ============================================================================

SKYFIELD_URL = os.getenv("SKYFIELD_URL", "http://caelum-skyfield:8001")

# Minimal fallback if Skyfield is still starting up when the agent boots
_FALLBACK_CATALOG: Dict[str, Dict[str, Any]] = {
    "Mercury": {"type": "planet", "category": "planets"},
    "Venus": {"type": "planet", "category": "planets"},
    "Mars": {"type": "planet", "category": "planets"},
    "Jupiter": {"type": "planet", "category": "planets"},
    "Saturn": {"type": "planet", "category": "planets"},
    "Uranus": {"type": "planet", "category": "planets"},
    "Neptune": {"type": "planet", "category": "planets"},
    "Moon": {"type": "natural_satellite", "category": "planets"},
    "Sun": {"type": "star", "category": "planets"},
}

VALID_ACTIONS = {
    "get_visible_objects",
    "get_object_details",
    "get_object_history",
}


def load_dynamic_catalog() -> Dict[str, Dict[str, Any]]:
    """Fetch the authoritative celestial catalog from caelum-skyfield."""
    catalog: Dict[str, Dict[str, Any]] = {}
    try:
        resp = requests.get(f"{SKYFIELD_URL}/catalog", timeout=5)
        resp.raise_for_status()
        raw = resp.json()

        # Estrae il dizionario interno se /catalog è incapsulato (es. {"catalog": {...}} o {"data": {...}})
        if isinstance(raw, dict):
            if "catalog" in raw and isinstance(raw["catalog"], dict):
                raw = raw["catalog"]
            elif "data" in raw and isinstance(raw["data"], dict):
                raw = raw["data"]

        for category in ["planets", "stars", "deep_sky", "constellations"]:
            for item in raw.get(category, []):
                name = item.get("name")
                if name:
                    catalog[name] = {
                        "type": item.get("type", category),
                        "category": category,
                        "messier": item.get("messier"),
                        "abbreviation": item.get("abbreviation"),
                        "constellation": item.get("constellation"),
                    }

        if catalog:
            print(f"[Agent] Dynamic catalog loaded: {len(catalog)} objects -> {list(catalog.keys())}")
            return catalog
        else:
            print(f"[Agent] /catalog risposto 200 ma vuoto. Chiavi ricevute: {list(raw.keys()) if isinstance(raw, dict) else type(raw)}")
    except Exception as e:
        print(f"[Agent] Warning: could not fetch /catalog from {SKYFIELD_URL} ({e}). Using fallback.")

    return _FALLBACK_CATALOG.copy()


# ============================================================================
# Agent Class
# ============================================================================

class CaelumAgent:
    """
    Secure Caelum Agent.
    - Accepts ONLY structured input (no free text)
    - Syncs whitelist dynamically from Skyfield's celestial_catalog.json
    - Uses LangChain + Google Gemini INTERNALLY for narration
    """

    def __init__(
        self,
        model_name: str = "gemini-3.1-flash-lite",
        temperature: float = 0.7,
        debug: bool = False
    ):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
            timeout=60
        )

        self.catalog: Dict[str, Dict[str, Any]] = load_dynamic_catalog()
        self.debug = debug
        self.conversation_history: List[Dict[str, Any]] = []

    # ========================================================================
    # Validation Methods
    # ========================================================================

    def _ensure_catalog_loaded(self) -> None:
        """Retry fetching the full catalog if only the minimal fallback was loaded."""
        if len(self.catalog) <= len(_FALLBACK_CATALOG):
            self.catalog = load_dynamic_catalog()

    def _validate_celestial_body(self, body_name: Optional[str]) -> str:
        """Validate that the requested body exists in the Skyfield catalog."""
        if not body_name:
            raise ValueError("object_name is required")

        self._ensure_catalog_loaded()
        clean = body_name.strip()

        # 1. Case-insensitive match on primary name (covers planets, stars, deep sky, constellations)
        for key in self.catalog:
            if key.lower() == clean.lower():
                return key

        # 2. Match on Messier designation (e.g., "M31" -> "Andromeda Galaxy")
        for key, info in self.catalog.items():
            messier = info.get("messier")
            if messier and messier.lower() == clean.lower():
                return key

        # 3. Match on constellation abbreviation (e.g., "Ori" -> "Orion")
        for key, info in self.catalog.items():
            abbr = info.get("abbreviation")
            if abbr and abbr.lower() == clean.lower():
                return key

        raise ValueError(
            f"'{body_name}' is not a valid celestial body in the catalog. "
            f"Valid bodies: {', '.join(sorted(self.catalog.keys()))}"
        )

    def _validate_action(self, action: str) -> str:
        """Validate that the action is allowed."""
        if action not in VALID_ACTIONS:
            raise ValueError(
                f"'{action}' is not a valid action. "
                f"Valid actions: {', '.join(sorted(VALID_ACTIONS))}"
            )
        return action

    def _validate_location(self, latitude: Optional[float], longitude: Optional[float]) -> tuple:
        """Validate latitude and longitude."""
        if latitude is not None and (latitude < -90 or latitude > 90):
            raise ValueError("latitude must be between -90 and 90")
        if longitude is not None and (longitude < -180 or longitude > 180):
            raise ValueError("longitude must be between -180 and 180")
        return (latitude, longitude)

    # ========================================================================
    # Structured Processing Methods
    # ========================================================================

    def process_structured(
        self,
        action: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        object_name: Optional[str] = None,
        timestamp: Optional[str] = None,
        include_planets: bool = True,
        include_stars: bool = True,
        include_deep_sky: bool = True,
        include_constellations: bool = True
    ) -> Dict[str, Any]:
        """
        Process a STRUCTURED request (no free text input).
        Uses LangChain + Google Gemini INTERNALLY for narration.
        """
        self.conversation_history.append({
            "role": "user",
            "action": action,
            "object_name": object_name,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": timestamp or datetime.utcnow().isoformat() + "Z"
        })

        self._validate_action(action)

        validated_name: Optional[str] = None
        if action in ["get_object_details", "get_object_history"]:
            validated_name = self._validate_celestial_body(object_name)

        self._validate_location(latitude, longitude)

        if action == "get_visible_objects":
            result = self._process_visible_objects(
                latitude, longitude, timestamp,
                include_planets, include_stars, include_deep_sky, include_constellations
            )
        elif action == "get_object_details":
            result = self._process_object_details(
                validated_name, latitude, longitude, timestamp  # type: ignore[arg-type]
            )
        elif action == "get_object_history":
            result = self._process_object_history(validated_name)  # type: ignore[arg-type]
        else:
            raise ValueError(f"Unknown action: {action}")

        self.conversation_history.append({
            "role": "assistant",
            "response": result.get("response", ""),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

        return result

    def _process_visible_objects(
        self,
        latitude: Optional[float],
        longitude: Optional[float],
        timestamp: Optional[str],
        include_planets: bool,
        include_stars: bool,
        include_deep_sky: bool,
        include_constellations: bool
    ) -> Dict[str, Any]:
        """Get visible celestial objects and narrate them."""
        if latitude is None or longitude is None:
            raise ValueError("latitude and longitude are required for this action")

        sky_data = self._fetch_sky_safe(
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
            include_planets=include_planets,
            include_stars=include_stars,
            include_deep_sky=include_deep_sky,
            include_constellations=include_constellations
        )

        response = self._narrate_visible_objects(sky_data)

        return {
            "response": response,
            "data": {
                "sky": sky_data,
                "action": "get_visible_objects"
            },
            "tool_calls": [
                {
                    "name": "get_visible_sky_pills",
                    "arguments": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "timestamp": timestamp
                    }
                }
            ],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def _process_object_details(
        self,
        object_name: str,
        latitude: Optional[float],
        longitude: Optional[float],
        timestamp: Optional[str]
    ) -> Dict[str, Any]:
        """Get details and history for a specific celestial object (including constellations)."""
        obj_info = self.catalog.get(object_name, {})
        obj_type = obj_info.get("type", "celestial_body")

        # Safely query Neo4j (constellations/stars may return not_found or empty missions)
        history_data = self._fetch_history_safe(object_name)

        # Get visibility info if location provided
        sky_data = None
        is_visible = None
        object_sky_details = None

        if latitude is not None and longitude is not None:
            sky_data = self._fetch_sky_safe(
                latitude=latitude,
                longitude=longitude,
                timestamp=timestamp,
                include_planets=True,
                include_stars=True,
                include_deep_sky=True,
                include_constellations=True
            )
            visible_objects = sky_data.get("visible_objects", [])
            for obj in visible_objects:
                name_in_sky = obj.get("object", obj.get("name", ""))
                if name_in_sky.lower() == object_name.lower():
                    is_visible = True
                    object_sky_details = obj
                    break
            if is_visible is None:
                is_visible = False

        response = self._narrate_object_details(
            object_name=object_name,
            obj_type=obj_type,
            history_data=history_data,
            sky_details=object_sky_details,
            is_visible=is_visible
        )

        return {
            "response": response,
            "data": {
                "object_name": object_name,
                "type": obj_type,
                "history": history_data,
                "sky": sky_data,
                "object_position": object_sky_details,
                "is_visible": is_visible,
                "action": "get_object_details"
            },
            "tool_calls": [
                {
                    "name": "get_celestial_history",
                    "arguments": {"celestial_body": object_name}
                },
                {
                    "name": "get_visible_sky_pills",
                    "arguments": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "timestamp": timestamp
                    }
                }
            ],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def _process_object_history(self, object_name: str) -> Dict[str, Any]:
        """Get only exploration history for a specific celestial object."""
        history_data = self._fetch_history_safe(object_name)
        response = self._narrate_object_history(object_name, history_data)

        return {
            "response": response,
            "data": {
                "object_name": object_name,
                "history": history_data,
                "action": "get_object_history"
            },
            "tool_calls": [
                {
                    "name": "get_celestial_history",
                    "arguments": {"celestial_body": object_name}
                }
            ],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    # ========================================================================
    # Safe Tool Wrappers
    # ========================================================================

    def _fetch_sky_safe(
        self,
        latitude: float,
        longitude: float,
        timestamp: Optional[str],
        include_planets: bool = True,
        include_stars: bool = True,
        include_deep_sky: bool = True,
        include_constellations: bool = True
    ) -> Dict[str, Any]:
        """Call get_visible_sky_pills safely, supporting tools with or without include_constellations."""
        try:
            return get_visible_sky_pills(
                latitude=latitude,
                longitude=longitude,
                timestamp=timestamp,
                include_planets=include_planets,
                include_stars=include_stars,
                include_deep_sky=include_deep_sky,
                include_constellations=include_constellations
            )
        except TypeError:
            # Backward compatibility if app/tools.py signature doesn't expose include_constellations yet
            return get_visible_sky_pills(
                latitude=latitude,
                longitude=longitude,
                timestamp=timestamp,
                include_planets=include_planets,
                include_stars=include_stars,
                include_deep_sky=include_deep_sky
            )

    def _fetch_history_safe(self, object_name: str) -> Dict[str, Any]:
        """Query Neo4j history safely without failing on unseeded bodies like constellations."""
        try:
            data = get_celestial_history(object_name)
            if not isinstance(data, dict) or data.get("status") in ("error", "not_found"):
                return {
                    "status": "not_found",
                    "celestial_body": object_name,
                    "missions": [],
                    "spacecraft": [],
                    "events": [],
                    "organizations": []
                }
            return data
        except Exception as e:
            print(f"[Agent] Non-blocking graph lookup error for {object_name}: {e}")
            return {
                "status": "not_found",
                "celestial_body": object_name,
                "missions": [],
                "spacecraft": [],
                "events": [],
                "organizations": []
            }

    # ========================================================================
    # Narration Methods (Using Google Gemini via LangChain)
    # ========================================================================

    def _narrate_visible_objects(self, sky_data: Dict[str, Any]) -> str:
        """Use LLM to generate a human-readable narration of visible objects."""
        observer = sky_data.get("observer", {})
        visible_objects = sky_data.get("visible_objects", [])

        if not visible_objects:
            return "No celestial objects are currently visible from your location."

        location = (observer.get("latitude", 0), observer.get("longitude", 0))
        time_str = observer.get("time_utc", "now")

        planets = [o for o in visible_objects if o.get("category") == "planet"]
        stars = [o for o in visible_objects if o.get("category") == "star"]
        deep_sky = [o for o in visible_objects if o.get("category") == "deep_sky"]
        constellations = [o for o in visible_objects if o.get("category") == "constellation"]

        prompt = f"""
        You are an astronomical assistant. Create a beautiful, engaging narration 
        about the visible celestial objects for a user at latitude {location[0]}°, 
        longitude {location[1]}° at {time_str}.
        
        Include the following information:
        - A welcoming introduction
        - List of visible planets with their altitude and azimuth
        - List of visible bright stars with their constellation
        - List of visible deep sky objects and constellations
        
        Use markdown formatting (##, ###, **, *, -).
        Be concise but informative.
        
        Visible planets: {planets}
        Visible stars: {stars}
        Visible deep sky objects: {deep_sky}
        Visible constellations: {constellations}
        """

        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception:
            return self._format_visible_objects_simple(sky_data)

    def _narrate_object_details(
        self,
        object_name: str,
        obj_type: str,
        history_data: Dict[str, Any],
        sky_details: Optional[Dict[str, Any]],
        is_visible: Optional[bool]
    ) -> str:
        """Use LLM to generate a narration about a specific celestial object."""
        prompt = f"""
        You are an astronomical assistant. Create a beautiful, engaging narration 
        about {object_name} (type: {obj_type}).
        
        Include the following information:
        - A welcoming introduction about {object_name}
        - Scientific and astronomical/mythological context about {object_name}
        - Human exploration history ONLY if missions exist in the history data (skip or briefly note no direct missions for constellations/distant stars)
        - Current visibility and sky coordinates if available
        
        Use markdown formatting (##, ###, **, *, -).
        Be concise but informative.
        
        Object type: {obj_type}
        Is currently visible: {is_visible}
        Current sky coordinates: {sky_details}
        History data: {history_data}
        """

        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception:
            return self._format_object_details_simple(
                object_name, history_data, sky_details, is_visible
            )

    def _narrate_object_history(
        self,
        object_name: str,
        history_data: Dict[str, Any]
    ) -> str:
        """Use LLM to generate a narration about the history of a celestial object."""
        prompt = f"""
        You are an astronomical assistant. Create a beautiful, engaging narration 
        about the human exploration history of {object_name}.
        
        Focus on:
        - Space missions that explored {object_name}
        - Spacecraft involved
        - Key historical events
        - Organizations involved
        
        If no direct space missions exist in the history data, clearly state that no spacecraft has directly visited {object_name} and briefly share how humanity has studied it from Earth or space telescopes.
        
        Use markdown formatting (##, ###, **, *, -).
        Be concise but informative.
        
        History data: {history_data}
        """

        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception:
            return self._format_object_history_simple(object_name, history_data)

    # ========================================================================
    # Fallback Methods (Simple formatting without LLM)
    # ========================================================================

    def _format_visible_objects_simple(self, sky_data: Dict[str, Any]) -> str:
        """Simple fallback formatting for visible objects."""
        observer = sky_data.get("observer", {})
        visible_objects = sky_data.get("visible_objects", [])

        parts = [
            "## 🌌 Tonight's Sky",
            f"From your location at **Latitude: {observer.get('latitude', 0)}°, "
            f"Longitude: {observer.get('longitude', 0)}°** at **{observer.get('time_utc', 'now')}**, "
            f"you can see:",
            ""
        ]

        planets = [o for o in visible_objects if o.get("category") == "planet"]
        if planets:
            parts.append("### 🪐 Planets")
            for p in planets:
                parts.append(
                    f"- **{p.get('object', 'Unknown')}**: "
                    f"Altitude {p.get('altitude_degrees', 0)}°, "
                    f"Azimuth {p.get('azimuth_degrees', 0)}°"
                )
            parts.append("")

        stars = [o for o in visible_objects if o.get("category") == "star"]
        if stars:
            parts.append("### ⭐ Bright Stars")
            for s in stars:
                parts.append(
                    f"- **{s.get('object', 'Unknown')}**: "
                    f"Altitude {s.get('altitude_degrees', 0)}°, "
                    f"Azimuth {s.get('azimuth_degrees', 0)}°"
                )
            parts.append("")

        constellations = [o for o in visible_objects if o.get("category") == "constellation"]
        if constellations:
            parts.append("### ✨ Constellations")
            for c in constellations:
                parts.append(
                    f"- **{c.get('object', 'Unknown')}**: "
                    f"Altitude {c.get('altitude_degrees', 0)}°, "
                    f"Azimuth {c.get('azimuth_degrees', 0)}°"
                )
            parts.append("")

        if not visible_objects:
            parts.append("No celestial objects are currently visible from your location.")

        return "\n".join(parts)

    def _format_object_details_simple(
        self,
        object_name: str,
        history_data: Dict[str, Any],
        sky_details: Optional[Dict[str, Any]],
        is_visible: Optional[bool]
    ) -> str:
        """Simple fallback formatting for object details."""
        parts = [f"## 🌌 {object_name}"]

        if is_visible is True:
            alt = sky_details.get("altitude_degrees") if sky_details else None
            az = sky_details.get("azimuth_degrees") if sky_details else None
            coords = f" (Altitude: {alt}°, Azimuth: {az}°)" if alt is not None else ""
            parts.append(f"**Currently visible** from your location{coords}!")
        elif is_visible is False:
            parts.append("**Currently NOT visible** from your location.")
        parts.append("")

        context = history_data.get("context", history_data) if isinstance(history_data, dict) else {}
        missions = context.get("missions", []) if isinstance(context, dict) else []

        parts.append("## 🚀 Human Exploration History")
        if missions:
            parts.append("**Missions:**")
            for m in missions[:5]:
                date = m.get("launch_date", "Unknown date")
                parts.append(f"  - {m.get('name', 'Unknown')} (Launched: {date})")
        else:
            parts.append(f"No direct space exploration missions recorded for {object_name}.")

        return "\n".join(parts)

    def _format_object_history_simple(
        self,
        object_name: str,
        history_data: Dict[str, Any]
    ) -> str:
        """Simple fallback formatting for object history."""
        parts = [f"## 🚀 Human Exploration History: {object_name}", ""]

        context = history_data.get("context", history_data) if isinstance(history_data, dict) else {}
        missions = context.get("missions", []) if isinstance(context, dict) else []

        if missions:
            parts.append("**Missions:**")
            for m in missions[:10]:
                date = m.get("launch_date", "Unknown date")
                parts.append(f"  - {m.get('name', 'Unknown')} (Launched: {date})")
        else:
            parts.append(f"No direct space exploration missions recorded for {object_name}.")

        return "\n".join(parts)

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def reset(self) -> Dict[str, Any]:
        """Reset the agent's conversation history."""
        self.conversation_history = []
        return {
            "status": "success",
            "message": "Agent conversation history reset",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


# ============================================================================
# Factory and Singleton
# ============================================================================

def create_agent(
    model_name: str = "gemini-3.1-flash-lite",
    temperature: float = 0.7,
    debug: bool = False
) -> CaelumAgent:
    """Factory function to create a CaelumAgent instance."""
    return CaelumAgent(
        model_name=model_name,
        temperature=temperature,
        debug=debug
    )


_agent_instance: Optional[CaelumAgent] = None


def get_agent() -> CaelumAgent:
    """Get the global agent instance (singleton)."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = create_agent()
    return _agent_instance


# Backward compatibility
caelum_agent = get_agent()