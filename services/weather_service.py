"""
services/weather_service.py

Fetches live AQI + weather for EXACT coordinates (start location).
Cache key uses 4 decimal precision (~11m accuracy).
Cache TTL: 30 minutes (was 1 hour — reduced so location changes reflect faster).
"""

import urllib.request
import json
import logging
import random
import time

logger = logging.getLogger(__name__)

_CACHE: dict = {}
CACHE_TTL = 1800  # 30 minutes


def fetch_weather_aqi(lat: float, lon: float, city_name: str = "") -> dict:
    """
    Fetch weather + AQI for exact coordinates.
    Cache key = rounded to 4 decimal places (~11m grid).
    Falls back to city-profile mock if API unavailable.
    """
    # Round to 4 decimals for cache key (~11m accuracy)
    cache_key = f"{round(lat, 4)}_{round(lon, 4)}"
    cached = _CACHE.get(cache_key)
    if cached and (time.time() - cached[0]) < CACHE_TTL:
        logger.info(f"Weather cache hit for {lat:.4f},{lon:.4f}")
        return cached[1]

    data = _try_live_api(lat, lon)
    if not data:
        data = _mock_weather(city_name)
        data['source'] = 'mock'
    else:
        data['source'] = 'live'

    data['aqi_label'], data['aqi_color'] = aqi_label(data.get('aqi', 0))
    _CACHE[cache_key] = (time.time(), data)
    return data


def _try_live_api(lat: float, lon: float) -> dict | None:
    try:
        from django.conf import settings
        api_key = getattr(settings, 'OPENWEATHER_API_KEY', '')
        if not api_key or api_key == 'YOUR_OPENWEATHER_API_KEY':
            return None

        headers = {"User-Agent": "GeoComfortIQ/1.0"}
        result  = {}

        # Current weather at exact coords
        w_url = (f"https://api.openweathermap.org/data/2.5/weather"
                 f"?lat={lat}&lon={lon}&appid={api_key}&units=metric")
        with urllib.request.urlopen(
            urllib.request.Request(w_url, headers=headers), timeout=8
        ) as r:
            w = json.loads(r.read().decode())

        result['temperature']  = round(w['main']['temp'], 1)
        result['humidity']     = int(w['main']['humidity'])
        result['feels_like']   = round(w['main'].get('feels_like', w['main']['temp']), 1)
        result['weather_desc'] = w['weather'][0]['description'].title()
        result['wind_speed']   = round(w.get('wind', {}).get('speed', 0) * 3.6, 1)

        # Air pollution at exact coords
        a_url = (f"https://api.openweathermap.org/data/2.5/air_pollution"
                 f"?lat={lat}&lon={lon}&appid={api_key}")
        with urllib.request.urlopen(
            urllib.request.Request(a_url, headers=headers), timeout=8
        ) as r:
            a = json.loads(r.read().decode())

        comp      = a['list'][0]['components']
        owm_index = a['list'][0]['main']['aqi']
        aqi_map   = {1: 25, 2: 75, 3: 125, 4: 200, 5: 320}
        result['aqi']  = aqi_map.get(owm_index, 100)
        result['pm25'] = round(comp.get('pm2_5', 0), 1)
        result['pm10'] = round(comp.get('pm10',  0), 1)
        result['no2']  = round(comp.get('no2',   0), 1)
        result['o3']   = round(comp.get('o3',    0), 1)

        logger.info(f"Live weather at ({lat:.4f},{lon:.4f}): temp={result['temperature']} aqi={result['aqi']}")
        return result

    except Exception as e:
        logger.warning(f"OpenWeatherMap API error: {e}")
        return None


def aqi_label(aqi: float) -> tuple:
    if aqi <= 50:   return "Good",          "success"
    if aqi <= 100:  return "Moderate",      "warning"
    if aqi <= 200:  return "Unhealthy",     "orange"
    if aqi <= 300:  return "Very Unhealthy","danger"
    return               "Hazardous",       "dark-red"


def travel_advice(weather: dict) -> str:
    aqi   = weather.get('aqi', 0)
    temp  = weather.get('temperature', 30)
    humid = weather.get('humidity', 50)
    issues = []
    if aqi > 200:   issues.append("hazardous air quality (AQI > 200)")
    elif aqi > 100: issues.append("poor air quality (AQI > 100)")
    if temp > 42:   issues.append("extreme heat (> 42°C)")
    elif temp > 37: issues.append("high temperature (> 37°C)")
    if humid > 85:  issues.append("very high humidity (> 85%)")
    if not issues:
        return "Conditions are acceptable. Best travel: 6–9 AM or after 7 PM."
    return (f"Caution — {', '.join(issues)}. "
            f"Travel early morning (before 7 AM) or after sunset. Carry water.")


# ── City mock profiles ─────────────────────────────────────────────────────────
_CITY_PROFILES = {
    "lucknow":   {"temp":(30,38),"humidity":(45,65),"aqi":(120,180),"pm25":(50,90), "pm10":(80,150), "wind":(5,15)},
    "delhi":     {"temp":(32,42),"humidity":(30,50),"aqi":(180,350),"pm25":(90,200),"pm10":(150,300),"wind":(3,12)},
    "mumbai":    {"temp":(28,33),"humidity":(70,90),"aqi":(80,140), "pm25":(30,70), "pm10":(50,110), "wind":(8,20)},
    "bengaluru": {"temp":(22,28),"humidity":(55,75),"aqi":(60,110), "pm25":(25,55), "pm10":(40,90),  "wind":(6,16)},
    "hyderabad": {"temp":(28,36),"humidity":(40,60),"aqi":(90,150), "pm25":(40,80), "pm10":(65,130), "wind":(4,14)},
    "chennai":   {"temp":(30,36),"humidity":(65,85),"aqi":(70,130), "pm25":(30,65), "pm10":(50,100), "wind":(7,18)},
    "kolkata":   {"temp":(28,35),"humidity":(60,80),"aqi":(130,200),"pm25":(60,110),"pm10":(100,180),"wind":(4,12)},
    "jaipur":    {"temp":(32,44),"humidity":(20,45),"aqi":(100,180),"pm25":(45,95), "pm10":(80,160), "wind":(6,18)},
}
_DEFAULT = {"temp":(28,35),"humidity":(50,65),"aqi":(100,160),"pm25":(45,85),"pm10":(75,140),"wind":(5,15)}

def _mock_weather(city_name: str) -> dict:
    p   = _CITY_PROFILES.get(city_name.lower().strip(), _DEFAULT)
    rnd = lambda r: round(random.uniform(*r), 1)
    return {
        "temperature":  rnd(p["temp"]),
        "humidity":     int(rnd(p["humidity"])),
        "aqi":          int(rnd(p["aqi"])),
        "pm25":         rnd(p["pm25"]),
        "pm10":         rnd(p["pm10"]),
        "wind_speed":   rnd(p["wind"]),
        "feels_like":   round(rnd(p["temp"]) + random.uniform(-2, 3), 1),
        "weather_desc": random.choice(["Clear Sky","Partly Cloudy","Haze","Sunny"]),
        "no2":          round(random.uniform(20, 80), 1),
        "o3":           round(random.uniform(30, 90), 1),
    }
