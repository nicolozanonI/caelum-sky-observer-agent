"""
Skyfield Engine for the caelum-skyfield microservice.
Handles astronomical calculations using Skyfield and JPL ephemeris.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import pytz
from skyfield.api import Loader, Topos, Star
from skyfield.jpllib import SpiceKernel

# Punta alla cartella app/ (risalendo da app/core/ o app/services/)
BASE_APP_DIR = Path(__file__).resolve().parent.parent
SKYFIELD_CACHE_DIR = BASE_APP_DIR / "data" / "cache"
SKYFIELD_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class SkyfieldEngine:
    """Engine for calculating positions of natural celestial bodies."""

    def __init__(self):
        """Initialize the Skyfield engine with ephemeris data."""
        bsp_path = SKYFIELD_CACHE_DIR / "de421.bsp"
        print(f"[Skyfield] Cerco effemeridi in: {bsp_path}")

        # builtin=True impedisce il download di finals2000A.all / deltat
        loader = Loader(str(SKYFIELD_CACHE_DIR), verbose=True)
        self.ts = loader.timescale(builtin=True)

        if bsp_path.exists() and bsp_path.stat().st_size > 0:
            print(f"[Skyfield] File locale trovato ({bsp_path.stat().st_size} bytes). Caricamento offline...")
            # SpiceKernel legge SOLO da disco: zero chiamate di rete possibili
            self.planets = SpiceKernel(str(bsp_path))
        else:
            print(f"[Skyfield] ATTENZIONE: {bsp_path} non trovato nel container! Avvio download...")
            self.planets = loader('de421.bsp')

        self.earth = self.planets['earth']
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> Dict[str, Any]:
        """Load the celestial catalog from JSON file."""
        catalog_path = BASE_APP_DIR / "data" / "celestial_catalog.json"
        print(f"[Skyfield] Cerco catalogo in: {catalog_path}")
        if not catalog_path.exists():
            raise FileNotFoundError(f"Catalogo celeste non trovato in: {catalog_path}")

        with open(catalog_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_planet(self, name: str):
        """Get a planet from the ephemeris data."""
        name_map = {
            "Mercury": "mercury",
            "Venus": "venus",
            "Mars": "mars",
            "Jupiter": "jupiter barycenter",
            "Saturn": "saturn barycenter",
            "Uranus": "uranus barycenter",
            "Neptune": "neptune barycenter",
            "Moon": "moon",
            "Sun": "sun",
        }
        planet_key = name_map.get(name.strip().capitalize(), name.lower())
        try:
            return self.planets[planet_key]
        except KeyError:
            return None
    
    def get_star_position(self, ra_hours: float, dec_degrees: float):
        """Create a star position from Right Ascension and Declination."""
        return Star(ra_hours=ra_hours, dec_degrees=dec_degrees)
    
    def calculate_sky(
        self,
        latitude: float,
        longitude: float,
        target_time: Optional[datetime] = None,
        include_planets: bool = True,
        include_stars: bool = True,
        include_deep_sky: bool = True,
        include_constellations: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate visible celestial bodies for a given observer location and time.
        
        Args:
            latitude: Observer's latitude in degrees
            longitude: Observer's longitude in degrees
            target_time: UTC datetime for observation
            include_planets: Whether to include planets
            include_stars: Whether to include stars
            include_deep_sky: Whether to include deep sky objects
            include_constellations: Whether to include constellations
        
        Returns:
            Dictionary containing observer info and list of visible objects
        """
        if target_time is None:
            target_time = datetime.now(pytz.utc)
        else:
            if target_time.tzinfo is None:
                target_time = pytz.utc.localize(target_time)
        
        observer_location = self.earth + Topos(
            latitude_degrees=latitude,
            longitude_degrees=longitude
        )
        
        t = self.ts.from_datetime(target_time)
        visible_objects = []

        # Calculate planet positions (ephemeris bodies: planets, Moon, Sun)
        if include_planets:
            planet_list = self.catalog.get("planets", [])
            for planet_info in planet_list:
                planet_name = planet_info.get("name", "")
                body_type = planet_info.get("type", "planet")
                body = self.get_planet(planet_name)

                if body is not None:
                    astrometric = observer_location.at(t).observe(body)
                    alt, az, distance = astrometric.apparent().altaz()

                    visible_objects.append({
                        "object": planet_name,
                        "type": body_type,
                        "category": body_type,
                        "altitude_degrees": float(round(alt.degrees, 2)),
                        "azimuth_degrees": float(round(az.degrees, 2)),
                        "distance_au": float(round(distance.au, 4)),
                        "visible": bool(alt.degrees > 0),
                        "magnitude": planet_info.get("magnitude")
                    })
        
        # Calculate star positions
        if include_stars:
            star_list = self.catalog.get("stars", [])
            for star_info in star_list:
                star_name = star_info.get("name", "")
                ra_hours = star_info.get("ra_hours", 0)
                dec_degrees = star_info.get("dec_degrees", 0)
                
                star_pos = self.get_star_position(ra_hours, dec_degrees)
                astrometric = observer_location.at(t).observe(star_pos)
                alt, az, distance = astrometric.apparent().altaz()
                
                visible_objects.append({
                    "object": star_name,
                    "type": "star",
                    "category": "star",
                    "altitude_degrees": float(round(alt.degrees, 2)),
                    "azimuth_degrees": float(round(az.degrees, 2)),
                    "distance_light_years": star_info.get("distance_ly"),
                    "visible": bool(alt.degrees > 0),
                    "magnitude": star_info.get("magnitude"),
                    "constellation": star_info.get("constellation")
                })
        
        # Calculate deep sky object positions
        if include_deep_sky:
            deep_sky_list = self.catalog.get("deep_sky", [])
            for ds_info in deep_sky_list:
                ds_name = ds_info.get("name", "")
                ra_hours = ds_info.get("ra_hours", 0)
                dec_degrees = ds_info.get("dec_degrees", 0)
                
                ds_pos = self.get_star_position(ra_hours, dec_degrees)
                astrometric = observer_location.at(t).observe(ds_pos)
                alt, az, distance = astrometric.apparent().altaz()
                
                visible_objects.append({
                    "object": ds_name,
                    "type": ds_info.get("type", "deep_sky"),
                    "category": "deep_sky",
                    "altitude_degrees": float(round(alt.degrees, 2)),
                    "azimuth_degrees": float(round(az.degrees, 2)),
                    "distance_light_years": ds_info.get("distance_ly"),
                    "visible": bool(alt.degrees > 0),
                    "magnitude": ds_info.get("magnitude"),
                    "messier": ds_info.get("messier"),
                    "constellation": ds_info.get("constellation")
                })
        
        # Calculate constellation centroids
        if include_constellations:
            constellation_list = self.catalog.get("constellations", [])
            for const_info in constellation_list:
                const_name = const_info.get("name", "")
                ra_hours = const_info.get("ra_hours", 0)
                dec_degrees = const_info.get("dec_degrees", 0)
                
                const_pos = self.get_star_position(ra_hours, dec_degrees)
                astrometric = observer_location.at(t).observe(const_pos)
                alt, az, distance = astrometric.apparent().altaz()
                
                visible_objects.append({
                    "object": const_name,
                    "type": "constellation",
                    "category": "constellation",
                    "altitude_degrees": float(round(alt.degrees, 2)),
                    "azimuth_degrees": float(round(az.degrees, 2)),
                    "visible": bool(alt.degrees > 0),
                    "abbreviation": const_info.get("abbreviation")
                })
        
        # Filter to only visible objects
        visible_only = [obj for obj in visible_objects if obj["visible"]]
        
        return {
            "observer": {
                "latitude": latitude,
                "longitude": longitude,
                "time_utc": target_time.isoformat(),
                "timestamp": target_time.timestamp()
            },
            "visible_objects": visible_only,
            "total_objects": len(visible_objects),
            "visible_count": len(visible_only)
        }
    
    def get_object_position(
        self,
        object_name: str,
        latitude: float,
        longitude: float,
        target_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get position of a specific celestial object."""
        if target_time is None:
            target_time = datetime.now(pytz.utc)
        else:
            if target_time.tzinfo is None:
                target_time = pytz.utc.localize(target_time)
        
        observer_location = self.earth + Topos(
            latitude_degrees=latitude,
            longitude_degrees=longitude
        )
        
        t = self.ts.from_datetime(target_time)
        
        # Try to find the object
        # Check planets / ephemeris bodies first
        body = self.get_planet(object_name)
        if body is not None:
            catalog_entry = next(
                (p for p in self.catalog.get("planets", []) if p.get("name", "").lower() == object_name.lower()),
                {}
            )
            body_type = catalog_entry.get("type", "planet")
            astrometric = observer_location.at(t).observe(body)
            alt, az, distance = astrometric.apparent().altaz()
            return {
                "object": object_name,
                "type": body_type,
                "category": body_type,
                "altitude_degrees": float(round(alt.degrees, 2)),
                "azimuth_degrees": float(round(az.degrees, 2)),
                "distance_au": float(round(distance.au, 4)),
                "visible": bool(alt.degrees > 0)
            }
        
        # Check catalog for stars, deep sky, etc.
        for category in ["stars", "deep_sky", "constellations"]:
            for item in self.catalog.get(category, []):
                if item.get("name", "").lower() == object_name.lower() or \
                   item.get("name", "") == object_name or \
                   (category == "deep_sky" and item.get("messier", "") == object_name):
                    ra_hours = item.get("ra_hours", 0)
                    dec_degrees = item.get("dec_degrees", 0)
                    
                    pos = self.get_star_position(ra_hours, dec_degrees)
                    astrometric = observer_location.at(t).observe(pos)
                    alt, az, distance = astrometric.apparent().altaz()
                    
                    result = {
                        "object": object_name,
                        "type": item.get("type", category),
                        "category": category,
                        "altitude_degrees": float(round(alt.degrees, 2)),
                        "azimuth_degrees": float(round(az.degrees, 2)),
                        "visible": alt.degrees > 0
                    }
                    
                    if category == "stars":
                        result["distance_light_years"] = item.get("distance_ly")
                        result["constellation"] = item.get("constellation")
                    elif category == "deep_sky":
                        result["distance_light_years"] = item.get("distance_ly")
                        result["messier"] = item.get("messier")
                    
                    return result
        
        return {"error": f"Object '{object_name}' not found in catalog"}


# Global engine instance
sky_engine = SkyfieldEngine()
