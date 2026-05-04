"""
services/route_service.py  — Phase 5

Fetches real walking/driving route between two coordinates
using OSRM (Open Source Routing Machine) — completely free, no API key.

Returns route geometry (list of [lat, lon] points) for Leaflet.js polyline,
plus distance (km) and duration (minutes).
"""

import urllib.request
import urllib.parse
import json
import logging

logger = logging.getLogger(__name__)

OSRM_BASE = "https://router.project-osrm.org/route/v1"


def get_route(start_lat: float, start_lon: float,
              end_lat: float,   end_lon: float,
              mode: str = "driving") -> dict:
    """
    Fetch route from OSRM between two coordinates.

    Args:
        start_lat, start_lon : origin coordinates
        end_lat,   end_lon   : destination coordinates
        mode                 : 'driving' | 'walking' | 'cycling'

    Returns dict:
        {
          'coords'  : [[lat, lon], ...],   # polyline points for Leaflet
          'distance': float,               # km
          'duration': float,               # minutes
          'found'   : bool,
        }
    """
    if not all([start_lat, start_lon, end_lat, end_lon]):
        return _empty_route()

    # OSRM expects lon,lat order
    coords_str = f"{start_lon},{start_lat};{end_lon},{end_lat}"
    params = urllib.parse.urlencode({
        "overview":    "full",
        "geometries":  "geojson",
        "steps":       "false",
    })
    url = f"{OSRM_BASE}/{mode}/{coords_str}?{params}"

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "GeoComfortIQ/1.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())

        if data.get("code") != "Ok" or not data.get("routes"):
            logger.warning(f"OSRM returned no route: {data.get('code')}")
            return _empty_route()

        route    = data["routes"][0]
        geometry = route["geometry"]["coordinates"]   # [[lon, lat], ...]

        # Flip to [lat, lon] for Leaflet
        coords = [[pt[1], pt[0]] for pt in geometry]

        return {
            "coords":   coords,
            "distance": round(route["distance"] / 1000, 2),   # m → km
            "duration": round(route["duration"] / 60, 1),     # s → min
            "found":    True,
        }

    except Exception as e:
        logger.warning(f"OSRM routing error: {e}")
        return _empty_route()


def _empty_route() -> dict:
    return {"coords": [], "distance": None, "duration": None, "found": False}
