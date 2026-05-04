"""
GeoComfortIQ — Central Configuration File
All tunable parameters live here.
"""

# ─── City Registry ────────────────────────────────────────────────────────────
# Add new cities here. 'image' is relative to data/cities/
CITIES = {
    "lucknow": {
        "display": "Lucknow",
        "state": "Uttar Pradesh",
        "lat": 26.8467,
        "lon": 80.9462,
        "image": "lucknow.jpg",
        "weather_city": "Lucknow",
    },
    "delhi": {
        "display": "New Delhi",
        "state": "Delhi",
        "lat": 28.6139,
        "lon": 77.2090,
        "image": "delhi.jpg",
        "weather_city": "Delhi",
    },
    "mumbai": {
        "display": "Mumbai",
        "state": "Maharashtra",
        "lat": 19.0760,
        "lon": 72.8777,
        "image": "mumbai.jpg",
        "weather_city": "Mumbai",
    },
    "bengaluru": {
        "display": "Bengaluru",
        "state": "Karnataka",
        "lat": 12.9716,
        "lon": 77.5946,
        "image": "bengaluru.jpg",
        "weather_city": "Bangalore",
    },
    "hyderabad": {
        "display": "Hyderabad",
        "state": "Telangana",
        "lat": 17.3850,
        "lon": 78.4867,
        "image": "hyderabad.jpg",
        "weather_city": "Hyderabad",
    },
    "chennai": {
        "display": "Chennai",
        "state": "Tamil Nadu",
        "lat": 13.0827,
        "lon": 80.2707,
        "image": "chennai.jpg",
        "weather_city": "Chennai",
    },
    "kolkata": {
        "display": "Kolkata",
        "state": "West Bengal",
        "lat": 22.5726,
        "lon": 88.3639,
        "image": "kolkata.jpg",
        "weather_city": "Kolkata",
    },
    "jaipur": {
        "display": "Jaipur",
        "state": "Rajasthan",
        "lat": 26.9124,
        "lon": 75.7873,
        "image": "jaipur.jpg",
        "weather_city": "Jaipur",
    },
}

# ─── Comfort Score Weights ─────────────────────────────────────────────────────
# Must sum to 1.0
# Positive weight = higher value → better comfort
# Negative weight = higher value → worse comfort
COMFORT_WEIGHTS = {
    "green_pct":      +0.30,   # More green = better
    "shade_pct":      +0.20,   # More shade = better
    "dust_pct":       -0.20,   # More dust = worse
    "builtup_pct":    -0.15,   # More concrete = slightly worse
    "congestion_pct": -0.15,   # More congestion = worse
}

# ─── Risk Zone Thresholds ──────────────────────────────────────────────────────
RISK_THRESHOLDS = {
    "safe":     (70, 100),
    "moderate": (40, 70),
    "risky":    (0,  40),
}

# ─── KMeans Settings ──────────────────────────────────────────────────────────
KMEANS_CLUSTERS = 3          # Safe / Moderate / Risky
KMEANS_RANDOM_STATE = 42

# ─── AQI Thresholds (WHO Guidelines) ──────────────────────────────────────────
AQI_LEVELS = {
    "Good":       (0,   50),
    "Moderate":   (51,  100),
    "Unhealthy":  (101, 200),
    "Hazardous":  (201, 500),
}

# ─── Cache Settings ───────────────────────────────────────────────────────────
CACHE_TIMEOUT_SECONDS = 3600   # 1 hour for weather/AQI data
