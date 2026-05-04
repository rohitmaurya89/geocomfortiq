"""
apps/assistant/views.py
Gemini AI Assistant with comprehensive rule-based fallback.
"""

import json
import urllib.request
import urllib.error
import logging
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


def _get_gemini_key() -> str:
    key = os.environ.get('GEMINI_API_KEY', '')
    if key:
        return key
    try:
        from django.conf import settings
        return getattr(settings, 'GEMINI_API_KEY', '')
    except Exception:
        return ''


def _build_system_prompt(result=None) -> str:
    base = """You are GeoComfortIQ Assistant. GeoComfortIQ is a satellite-image-based Urban Outdoor Comfort Analysis System built as a final year engineering project.

PROJECT PURPOSE: Help citizens (elderly, children, outdoor workers, general public) choose safer and more comfortable outdoor routes in Indian cities by analyzing environmental conditions.

TECHNICAL STACK:
- Backend: Django 4.2 (Python)
- Image Analysis: OpenCV + NumPy (HSV pixel segmentation)
- Machine Learning: KMeans clustering (scikit-learn) — classifies zones into Safe/Moderate/Risky
- Deep Learning: DeepLabV3 ResNet-50 (PyTorch) — pretrained land-cover segmentation, inference only
- Maps: Leaflet.js with OSRM free routing (blue route like Google Maps)
- Charts: Chart.js (pie + bar)
- Satellite Data: ISRO Bhuvan / ESA Sentinel-2 (tci.jp2 = True Color Image)
- Weather/AQI: OpenWeatherMap API (live data)
- Geocoding: Nominatim (OpenStreetMap, free)
- Database: SQLite (development)
- AI Assistant: Google Gemini 1.5 Flash API

PARAMETERS ANALYZED:
- Green Cover %: vegetation pixels via HSV (Hue 35-90)
- Dust/Open Land %: bare soil pixels (Hue 10-32)
- Built-up %: concrete/road pixels (low saturation grey)
- Shade/Shadow %: dark pixels (brightness < 50)
- Water Body %: blue-dominant pixels
- Congestion %: Canny edge density (structural density proxy)
- Comfort Score (0-100): weighted formula = 50 + sum(weight × (param - 50))
  Green +0.30, Shade +0.20, Dust -0.20, Built-up -0.15, Congestion -0.15

INDICES:
- NDVI = (NIR - Red)/(NIR + Red): vegetation index, >0.3 = healthy green
- NDBI = (SWIR - NIR)/(SWIR + NIR): built-up index

Answer any question about this project thoroughly. Be helpful, clear, and concise."""

    if result:
        base += f"""

CURRENT ANALYSIS:
- City: {result.city.display_name}
- Route: {result.start_location} → {result.end_location}
- Comfort Score: {result.comfort_score:.1f}/100
- Risk: {result.risk_category.upper()}
- Green: {result.green_pct:.1f}%, Dust: {result.dust_pct:.1f}%
- Built-up: {result.builtup_pct:.1f}%, Shade: {result.shade_pct:.1f}%
- Congestion: {result.congestion_pct:.1f}%
- AQI: {result.aqi or 'N/A'}, Temp: {result.temperature or 'N/A'}°C"""

    return base


@csrf_exempt
@require_POST
def chat(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"reply": "Invalid request.", "source": "error"}, status=400)

    message   = body.get("message", "").strip()
    result_id = body.get("result_id")
    history   = body.get("history", [])

    if not message:
        return JsonResponse({"reply": "Please type a message.", "source": "error"})

    result = None
    if result_id:
        try:
            from apps.dashboard.models import AnalysisResult
            result = AnalysisResult.objects.select_related('city').get(id=result_id)
        except Exception:
            pass

    reply, source = _try_gemini_api(message, result, history)

    if reply is None:
        reply  = _rule_based_reply(message, result)
        source = "fallback"

    return JsonResponse({"reply": reply, "source": source})


def _try_gemini_api(message: str, result, history: list) -> tuple:
    api_key = _get_gemini_key()

    if not api_key:
        logger.warning("GEMINI_API_KEY is empty. Check your .env file.")
        return None, None

    logger.info(f"Calling Gemini API (key length={len(api_key)})...")

    try:
        system_prompt = _build_system_prompt(result)
        contents = []

        for h in history[-6:]:
            role = "user" if h.get("role") == "user" else "model"
            if h.get("content"):
                contents.append({"role": role, "parts": [{"text": h["content"]}]})

        contents.append({"role": "user", "parts": [{"text": message}]})

        payload = json.dumps({
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {"maxOutputTokens": 500, "temperature": 0.7}
        }).encode()

        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"gemini-1.5-flash:generateContent?key={api_key}")

        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode())

        reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        logger.info("Gemini API success.")
        return reply, "gemini"

    except urllib.error.HTTPError as e:
        err = e.read().decode()
        logger.warning(f"Gemini HTTP {e.code}: {err}")
        return None, None
    except Exception as e:
        logger.warning(f"Gemini error: {e}")
        return None, None


def _rule_based_reply(message: str, result) -> str:
    msg = message.lower().strip()

    # ── Specific terms FIRST (before generic project/explain checks) ──────────

    if "ndvi" in msg:
        return ("🌿 NDVI (Normalized Difference Vegetation Index):\n"
                "Formula: (NIR − Red) / (NIR + Red)\n"
                "Range: −1 to +1\n"
                "• Above 0.3 = healthy vegetation\n"
                "• 0.1–0.3 = sparse vegetation\n"
                "• Below 0.1 = bare soil or urban area\n"
                "Requires NIR band (B08) from Sentinel-2.")

    if "ndbi" in msg:
        return ("🏙️ NDBI (Normalized Difference Built-up Index):\n"
                "Formula: (SWIR − NIR) / (SWIR + NIR)\n"
                "Higher value = more urban built-up surface.\n"
                "Requires SWIR band (B11) from Sentinel-2.")

    if any(w in msg for w in ["aqi", "air quality", "pm2.5", "pm10", "pollution"]):
        return ("🌫️ AQI (Air Quality Index):\n"
                "• 0–50: Good ✅\n"
                "• 51–100: Moderate ⚠️\n"
                "• 101–200: Unhealthy 😷\n"
                "• 200+: Hazardous 🚨\n\n"
                "Source: OpenWeatherMap API (live data)\n"
                "PM2.5 > 60 µg/m³ = wear N95 mask\n"
                "PM10 > 100 µg/m³ = avoid outdoor for sensitive groups")

    if any(w in msg for w in ["kmeans", "k-means", "clustering", "machine learning"]):
        return ("🤖 KMeans Clustering:\n"
                "• Unsupervised ML — no labeled training data needed\n"
                "• K=3 clusters: Safe, Moderate, Risky\n"
                "• Input features: Green%, Dust%, Built-up%, Shade%, Congestion%\n"
                "• Cluster with highest green+shade = Safe\n"
                "• Cluster with highest dust+congestion = Risky")

    if any(w in msg for w in ["deeplabv3", "deep learning", "neural", "pytorch", "dl model"]):
        return ("🧠 Deep Learning — DeepLabV3:\n"
                "• Model: DeepLabV3 ResNet-50 (torchvision)\n"
                "• Pretrained on Pascal VOC — inference only, no training\n"
                "• Segments image into land-cover classes\n"
                "• Blends with OpenCV: 60% OpenCV + 40% DeepLabV3\n"
                "• Auto-disabled if PyTorch not installed")

    if any(w in msg for w in ["comfort score", "score formula", "how is score", "weighted"]):
        return ("📊 Comfort Score (0–100):\n"
                "Formula: 50 + Σ(weight × (param − 50))\n\n"
                "Weights:\n"
                "• Green Cover: +0.30\n"
                "• Shade: +0.20\n"
                "• Dust: −0.20\n"
                "• Built-up: −0.15\n"
                "• Congestion: −0.15\n\n"
                "Score ≥ 70 = Safe ✅ | 40–70 = Moderate ⚠️ | < 40 = Risky 🚨")

    if any(w in msg for w in ["green cover", "green pct", "vegetation"]):
        return ("🌿 Green Cover %:\n"
                "• Pixels with green HSV hue (35–90°) detected via OpenCV\n"
                "• More green = cooler microclimate, better air quality\n"
                "• Has +0.30 weight in comfort score formula\n"
                "• Lucknow average: 15–25%")

    if any(w in msg for w in ["dust", "open land", "bare soil"]):
        return ("🌪️ Dust / Open Land %:\n"
                "• Sandy/brown pixels (HSV Hue 10–32°)\n"
                "• High dust = elevated PM10, poor air quality\n"
                "• Has −0.20 weight in comfort score formula\n"
                "• Above 35% is concerning for health")

    if any(w in msg for w in ["shade", "shadow"]):
        return ("☁️ Shade / Shadow %:\n"
                "• Very dark pixels (brightness < 50 in HSV)\n"
                "• More shade = less UV exposure, cooler temperature\n"
                "• Has +0.20 weight in comfort score formula")

    if any(w in msg for w in ["congestion", "edge density", "structural"]):
        return ("🚧 Congestion %:\n"
                "• Measured using Canny edge detection\n"
                "• More edges per pixel = denser structures\n"
                "• Proxy for structural congestion and poor airflow\n"
                "• Has −0.15 weight in comfort score formula\n"
                "• Separate metric — not part of land cover sum")

    if any(w in msg for w in ["built-up", "builtup", "concrete", "building"]):
        return ("🏢 Built-up %:\n"
                "• Grey/white pixels with low saturation (concrete, roads)\n"
                "• High built-up = urban heat island effect\n"
                "• Has −0.15 weight in comfort score formula")

    if any(w in msg for w in ["satellite", "sentinel", "bhuvan", "isro", "tci", "jp2", "band"]):
        return ("🛰️ Satellite Data:\n"
                "• Source: ISRO Bhuvan / ESA Sentinel-2\n"
                "• Resolution: 10m/pixel\n"
                "• Key file: tci.jp2 (True Color Image = RGB)\n"
                "• Other bands: B04 (Red), B08 (NIR), B11 (SWIR)\n"
                "• Stored in: dataset/final_dataset/<city>_dataset/\n"
                "• Data is stable — city structure doesn't change monthly")

    if any(w in msg for w in ["osrm", "routing", "road", "route", "map", "direction", "path"]):
        if result:
            icon = "✅" if result.risk_category == "safe" else ("⚠️" if result.risk_category == "moderate" else "🚨")
            return (f"{icon} Route: {result.start_location} → {result.end_location}\n"
                    f"Score: {result.comfort_score:.1f}/100 — {result.risk_category.upper()}\n"
                    f"Green: {result.green_pct:.1f}% | Dust: {result.dust_pct:.1f}%\n"
                    f"Route uses OSRM — real road network, blue polyline.")
        return ("Routes use OSRM (free, no API key).\n"
                "• Real road network from OpenStreetMap\n"
                "• Blue polyline with white border\n"
                "• Turn-by-turn directions in sidebar\n"
                "• Start = pulsing blue dot, End = red pin")

    if any(w in msg for w in ["time", "when", "best time", "travel time", "morning", "evening"]):
        return ("🕐 Best outdoor travel times:\n"
                "• 6–8 AM: Lowest temp, cleanest air ✅\n"
                "• 7–9 PM: Cooler after sunset ✅\n"
                "• Avoid 11 AM–4 PM: Peak heat + UV ❌\n"
                "• AQI > 150: Wear N95 mask always")

    if any(w in msg for w in ["elderly", "child", "sick", "pregnant", "health", "worker"]):
        return ("🏥 Safety by group:\n"
                "• Elderly & children: Score ≥ 70 only\n"
                "• Outdoor workers: N95 if AQI > 100\n"
                "• Pregnant: Avoid Dust > 30% or AQI > 100\n"
                "• General: Score 40–70 usable with care")

    if any(w in msg for w in ["tech", "stack", "framework", "django", "opencv", "tools"]):
        return ("🛠️ Technology Stack:\n"
                "• Backend: Django 4.2 (Python)\n"
                "• Image Analysis: OpenCV + NumPy\n"
                "• ML: KMeans (scikit-learn)\n"
                "• DL: DeepLabV3 ResNet-50 (PyTorch)\n"
                "• Maps: Leaflet.js + OSRM\n"
                "• Charts: Chart.js\n"
                "• Weather: OpenWeatherMap API\n"
                "• Database: SQLite")

    # ── Greetings ─────────────────────────────────────────────────────────────
    if any(w in msg for w in ["hello", "hi", "hey", "namaste"]):
        return ("👋 Hello! I'm GeoComfortIQ Assistant.\n"
                "Ask me about NDVI, AQI, comfort score, route safety, parameters, or this project.")

    # ── Project — LAST (most generic, catches remaining questions) ────────────
    if any(w in msg for w in ["project", "about", "explain", "describe", "purpose",
                               "objective", "goal", "overview", "what is", "tell me",
                               "geocomfort", "summary", "introduction"]):
        return ("GeoComfortIQ — Urban Outdoor Comfort Analysis System\n\n"
                "🎯 Purpose: Help citizens choose safer outdoor routes in Indian cities.\n\n"
                "⚙️ How it works:\n"
                "• Satellite imagery (Sentinel-2) analyzed using OpenCV\n"
                "• Parameters extracted: Green, Dust, Built-up, Shade, Water\n"
                "• KMeans ML classifies zones: Safe / Moderate / Risky\n"
                "• Comfort Score (0-100) computed using weighted formula\n"
                "• Live AQI + weather from OpenWeatherMap\n"
                "• Route shown on Leaflet map using OSRM routing\n\n"
                "🛠️ Tech: Django, OpenCV, KMeans, DeepLabV3, Leaflet.js")

    # ── Help ──────────────────────────────────────────────────────────────────
    if any(w in msg for w in ["help", "what can", "capabilities"]):
        return ("Ask me about:\n"
                "• NDVI, NDBI, AQI, Green Cover, Dust, Shade, Congestion\n"
                "• Comfort Score formula and weights\n"
                "• KMeans ML and DeepLabV3 DL\n"
                "• Satellite data and bands\n"
                "• Route analysis and travel tips\n"
                "• Project purpose and technology")

    return (f"I didn't understand '{message[:50]}'.\n"
            "Try: 'What is NDVI?', 'Explain comfort score', 'What is KMeans?', "
            "'Best time to travel?', or 'Tell me about this project'")