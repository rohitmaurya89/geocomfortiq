"""
services/geocoder.py

Three-tier geocoding for Indian localities:
  1. Hardcoded lookup (instant, works offline) — 80+ Lucknow localities + major cities
  2. Nominatim OSM (free, no key)
  3. City-centre fallback (map always shows something)
"""

import urllib.request
import urllib.parse
import json
import logging
import time

logger = logging.getLogger(__name__)
HEADERS = {"User-Agent": "GeoComfortIQ/1.0 (urban-comfort-analysis)"}

# ── Hardcoded locality database ────────────────────────────────────────────────
# Format: "locality name lowercase" : (lat, lon)
LOCALITY_DB = {

    # ── Lucknow localities ─────────────────────────────────────────────────────
    "hazratganj":               (26.8506, 80.9483),
    "gomti nagar":              (26.8538, 80.9928),
    "gomtinagar":               (26.8538, 80.9928),
    "jankipuram":               (26.9124, 80.9408),
    "jankipuram extension":     (26.9180, 80.9350),
    "aliganj":                  (26.8796, 80.9417),
    "indira nagar":             (26.8730, 81.0018),
    "indiranagar":              (26.8730, 81.0018),
    "vikas nagar":              (26.8921, 80.9628),
    "rajajipuram":              (26.8340, 80.9050),
    "mahanagar":                (26.8749, 80.9570),
    "alambagh":                 (26.8133, 80.9233),
    "aminabad":                 (26.8493, 80.9319),
    "charbagh":                 (26.8278, 80.9152),
    "lucknow junction":         (26.8281, 80.9150),
    "chowk":                    (26.8635, 80.9150),
    "kaiserbagh":                (26.8588, 80.9285),
    "hussainganj":               (26.8553, 80.9367),
    "ashok marg":               (26.8552, 80.9440),
    "lalbagh":                  (26.8473, 80.9278),
    "latouche road":            (26.8380, 80.9210),
    "naka":                     (26.8630, 80.9630),
    "naka hindola":             (26.8630, 80.9630),
    "nirala nagar":             (26.8741, 80.9730),
    "krishna nagar":            (26.8657, 80.9738),
    "rajendra nagar":           (26.8560, 80.9680),
    "sector b":                 (26.8670, 80.9850),
    "telibagh":                 (26.7986, 80.9444),
    "sushant golf city":        (26.7830, 80.9580),
    "faizabad road":            (26.8900, 81.0100),
    "sultanpur road":           (26.7900, 80.9800),
    "ring road":                (26.8500, 80.9700),
    "vrindavan yojana":         (26.8092, 80.9726),
    "vibhuti khand":            (26.8617, 80.9958),
    "sector 14":                (26.8700, 80.9950),
    "paper mill colony":        (26.8830, 80.9980),
    "new hyderabad":            (26.8690, 80.9260),
    "lko cantonment":           (26.8200, 80.9450),
    "cantonment":               (26.8200, 80.9450),
    "dilkusha":                 (26.8680, 80.9830),
    "sarojini nagar":           (26.8040, 80.9360),
    "chinhat":                  (26.8800, 81.0490),
    "transport nagar":          (26.9050, 80.9660),
    "kursi road":               (26.9100, 80.9840),
    "madiaon":                  (26.8980, 80.9200),
    "sitapur road":             (26.9200, 80.9300),
    "hardoi road":              (26.9300, 80.9100),
    "rae bareli road":          (26.7800, 80.9500),
    "mall avenue":              (26.8560, 80.9430),
    "moti mahal":               (26.8550, 80.9270),
    "naza bad":                 (26.8820, 80.9280),
    "bazaar khala":             (26.8600, 80.9180),
    "gokhale marg":             (26.8530, 80.9410),
    "hazratganj crossing":      (26.8506, 80.9483),
    "1090 crossing":            (26.8510, 80.9500),
    "daliganj":                 (26.8750, 80.9320),
    "nishatganj":               (26.8780, 80.9330),
    "gautam buddh marg":        (26.8540, 80.9380),
    "vikramaditya marg":        (26.8520, 80.9420),
    "kalidas marg":             (26.8550, 80.9390),
    "rana pratap marg":         (26.8480, 80.9440),
    "sapru marg":               (26.8530, 80.9460),
    "park road":                (26.8520, 80.9470),
    "butler palace":            (26.8450, 80.9680),
    "kapoorthala":              (26.8650, 80.9940),
    "lucknow zoo":              (26.8490, 80.9490),
    "bara imambara":            (26.8675, 80.9120),
    "rumi darwaza":             (26.8680, 80.9115),
    "la martiniere":            (26.8545, 80.9548),
    "sgpgi":                    (26.8039, 81.0016),
    "sanjay gandhi pgi":        (26.8039, 81.0016),
    "kgmu":                     (26.8614, 80.9484),
    "king george medical":      (26.8614, 80.9484),
    "lucknow university":       (26.8596, 80.9320),
    "iim lucknow":              (26.7742, 80.9768),
    "ito":                      (26.8581, 80.9406),
    "lda colony":               (26.8520, 80.9740),
    "awas vikas":               (26.8870, 80.9550),
    "sector h":                 (26.8700, 81.0000),
    "sector i":                 (26.8760, 81.0060),
    "sector j":                 (26.8780, 81.0120),

    # ── Delhi localities ───────────────────────────────────────────────────────
    "connaught place":          (28.6329, 77.2195),
    "cp":                       (28.6329, 77.2195),
    "chandni chowk":            (28.6506, 77.2295),
    "karol bagh":               (28.6519, 77.1906),
    "lajpat nagar":             (28.5676, 77.2434),
    "saket":                    (28.5244, 77.2066),
    "dwarka":                   (28.5921, 77.0460),
    "rohini":                   (28.7358, 77.1022),
    "pitampura":                (28.7003, 77.1311),
    "janakpuri":                (28.6289, 77.0831),
    "nehru place":              (28.5491, 77.2537),
    "south extension":          (28.5706, 77.2200),
    "greater kailash":          (28.5477, 77.2412),

    # ── Mumbai localities ──────────────────────────────────────────────────────
    "colaba":                   (18.9067, 72.8147),
    "bandra":                   (19.0596, 72.8295),
    "andheri":                  (19.1136, 72.8697),
    "dadar":                    (19.0178, 72.8478),
    "borivali":                 (19.2307, 72.8567),
    "powai":                    (19.1176, 72.9060),
    "lower parel":              (18.9948, 72.8259),
    "worli":                    (19.0177, 72.8178),

    # ── Bengaluru localities ───────────────────────────────────────────────────
    "mg road":                  (12.9751, 77.6186),
    "koramangala":              (12.9352, 77.6245),
    "indiranagar bangalore":    (12.9784, 77.6408),
    "whitefield":               (12.9698, 77.7499),
    "electronic city":          (12.8451, 77.6602),
    "jayanagar":                (12.9252, 77.5938),
    "marathahalli":             (12.9591, 77.6974),

    # ── City centres (used as last resort fallback) ────────────────────────────
    "lucknow":                  (26.8467, 80.9462),
    "delhi":                    (28.6139, 77.2090),
    "new delhi":                (28.6139, 77.2090),
    "mumbai":                   (19.0760, 72.8777),
    "bengaluru":                (12.9716, 77.5946),
    "bangalore":                (12.9716, 77.5946),
    "hyderabad":                (17.3850, 78.4867),
    "chennai":                  (13.0827, 80.2707),
    "kolkata":                  (22.5726, 88.3639),
    "jaipur":                   (26.9124, 75.7873),
    "pune":                     (18.5204, 73.8567),
    "ahmedabad":                (23.0225, 72.5714),
    "kanpur":                   (26.4499, 80.3319),
    "nagpur":                   (21.1458, 79.0882),
    "varanasi":                 (25.3176, 82.9739),
    "agra":                     (27.1767, 78.0081),
}


def geocode_location(place_name: str, city_hint: str = "") -> dict:
    """
    Returns dict: { lat, lon, display_name, geocoded: True/False }
    Tries hardcoded DB first (instant), then Nominatim, then city fallback.
    """
    # ── 1. Hardcoded DB lookup (instant) ──────────────────────────────────────
    key = place_name.strip().lower()
    if key in LOCALITY_DB:
        lat, lon = LOCALITY_DB[key]
        logger.info(f"Locality DB hit: '{place_name}' → {lat}, {lon}")
        return {"lat": lat, "lon": lon, "display_name": place_name, "geocoded": True}

    # Try partial match (e.g. "Jankipuram Ext" → "jankipuram extension")
    for db_key, coords in LOCALITY_DB.items():
        if key in db_key or db_key in key:
            lat, lon = coords
            logger.info(f"Locality DB partial match: '{place_name}' → '{db_key}' → {lat}, {lon}")
            return {"lat": lat, "lon": lon, "display_name": place_name, "geocoded": True}

    # ── 2. Nominatim API ───────────────────────────────────────────────────────
    result = _try_nominatim(place_name, city_hint)
    if result["lat"]:
        return result

    # ── 3. City-centre fallback ────────────────────────────────────────────────
    city_key = city_hint.strip().lower()
    if city_key in LOCALITY_DB:
        lat, lon = LOCALITY_DB[city_key]
        logger.warning(f"Using city centre fallback for '{place_name}' → {city_hint}")
        return {
            "lat": lat, "lon": lon,
            "display_name": f"{place_name} (approx. {city_hint} area)",
            "geocoded": False,
        }

    return {"lat": None, "lon": None, "display_name": place_name, "geocoded": False}


def _try_nominatim(place_name: str, city_hint: str, retries: int = 2) -> dict:
    query = f"{place_name}, {city_hint}, India" if city_hint else f"{place_name}, India"
    params = urllib.parse.urlencode({
        "q": query, "format": "json", "limit": 1,
        "addressdetails": 1, "countrycodes": "in",
    })
    url = f"https://nominatim.openstreetmap.org/search?{params}"

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=8 + attempt * 4) as r:
                data = json.loads(r.read().decode())
            if data:
                return {
                    "lat": float(data[0]["lat"]),
                    "lon": float(data[0]["lon"]),
                    "display_name": data[0].get("display_name", place_name),
                    "geocoded": True,
                }
            break
        except Exception as e:
            logger.warning(f"Nominatim attempt {attempt+1} for '{place_name}': {e}")
            if attempt < retries - 1:
                time.sleep(1)

    return {"lat": None, "lon": None, "display_name": place_name, "geocoded": False}
