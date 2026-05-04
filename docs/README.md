# 🛰️ GeoComfortIQ — Urban Outdoor Comfort Analysis System

Satellite-image-based comfort analysis for Indian cities.
Helps citizens (elderly, children, outdoor workers) choose safer routes
using OpenCV, KMeans ML, DeepLabV3 DL, live AQI, and interactive maps.

---

## ⚡ Quick Start (one command)

```bash
python setup.py
python manage.py runserver
```
Open: **http://127.0.0.1:8000**

---

## 📋 Manual Setup

```bash
# 1. Virtual environment
python -m venv venv
source venv/bin/activate          # Mac/Linux
venv\Scripts\activate             # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Database
python manage.py makemigrations
python manage.py migrate

# 4. Run
python manage.py runserver
```

---

## 🔑 API Keys (all optional — app works on mock data without them)

| Key | Purpose | Get it at |
|-----|---------|-----------|
| `OPENWEATHER_API_KEY` | Live AQI + weather | openweathermap.org (free) |
| `ANTHROPIC_API_KEY` | Claude AI assistant | console.anthropic.com |

Set in `.env` file (copy from `.env.example`) or directly in `geocomfortiq/settings.py`.

---

## 🗺️ Adding Satellite Images

1. Download from **ISRO Bhuvan** (bhuvan.nrsc.gov.in) or **Sentinel Hub**
2. Save to `data/cities/<cityslug>.jpg`
3. Supported slugs: `lucknow` `delhi` `mumbai` `bengaluru` `hyderabad` `chennai` `kolkata` `jaipur`

Without images → app uses realistic city-specific mock data automatically.

---

## 📁 Project Structure (45 files)

```
geocomfortiq/
├── manage.py                    # Django entry point
├── setup.py                     # Quick setup script
├── requirements.txt
├── .env.example                 # API key template
│
├── geocomfortiq/                # Django project config
│   ├── settings.py
│   └── urls.py
│
├── apps/
│   ├── dashboard/               # Main views, models, URLs
│   │   ├── models.py            # City + AnalysisResult DB models
│   │   ├── views.py             # Home, analyze, dashboard_detail
│   │   └── urls.py
│   ├── analysis/                # OpenCV + DL image analysis
│   │   ├── green.py             # Green cover extraction
│   │   ├── dust.py              # Dust/open land extraction
│   │   ├── builtup.py           # Built-up/concrete extraction
│   │   ├── shadow.py            # Shade/shadow extraction
│   │   ├── congestion.py        # Edge density congestion
│   │   ├── analyzer.py          # Orchestrator (OpenCV + DL blend)
│   │   └── dl_segmenter.py      # DeepLabV3 inference (Phase 6)
│   └── assistant/               # AI chatbot
│       └── views.py             # Claude API + rule-based fallback
│
├── services/
│   ├── geocoder.py              # Nominatim place → coordinates
│   ├── mock_analysis.py         # City-realistic stub data
│   ├── comfort_score.py         # Weighted formula + explain()
│   ├── kmeans_classifier.py     # KMeans zone classification
│   ├── weather_service.py       # OpenWeatherMap AQI + weather
│   └── route_service.py         # OSRM free routing API
│
├── config/
│   └── settings_config.py       # Cities, weights, thresholds ← tune here
│
├── templates/
│   ├── base/base.html           # Master layout + AI assistant panel
│   ├── home/index.html          # Landing page + route form
│   └── dashboard/detail.html   # Full analysis dashboard
│
├── static/
│   ├── css/main.css             # Complete dark design system
│   └── js/
│       ├── main.js
│       └── assistant.js         # Claude API chat + markdown render
│
├── data/cities/                 # ← Place satellite images here
└── docs/
    ├── README.md                # This file
    ├── TERMS.txt                # Technical definitions
    └── VIVA_NOTES.txt           # Q&A for viva
```

---

## 🗄️ Database Schema

### `dashboard_city`
| Field | Type | Description |
|-------|------|-------------|
| slug | VARCHAR | e.g. "lucknow" |
| display_name | VARCHAR | e.g. "Lucknow" |
| latitude / longitude | FLOAT | City centre |
| satellite_image | VARCHAR | Filename in data/cities/ |

### `dashboard_analysisresult`
| Field | Type | Description |
|-------|------|-------------|
| city | FK | → City |
| start_location / end_location | VARCHAR | User input |
| start_lat/lon / end_lat/lon | FLOAT | Geocoded coords |
| green_pct | FLOAT | 0–100 |
| dust_pct | FLOAT | 0–100 |
| builtup_pct | FLOAT | 0–100 |
| shade_pct | FLOAT | 0–100 |
| congestion_pct | FLOAT | 0–100 |
| water_pct | FLOAT | 0–100 |
| comfort_score | FLOAT | 0–100 |
| risk_category | VARCHAR | safe / moderate / risky |
| aqi / pm25 / pm10 | FLOAT | Live air quality |
| temperature / humidity | FLOAT | Live weather |
| dl_available | BOOL | Was DeepLabV3 used? |
| is_cached | BOOL | Served from cache? |
| created_at | DATETIME | Timestamp |

---

## ✅ Phase Completion Summary

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Django project + UI skeleton + DB models | ✅ |
| 2 | OpenCV: green, dust, builtup, shadow, congestion | ✅ |
| 3 | Comfort score formula + KMeans zone classification | ✅ |
| 4 | Live AQI + weather API with caching | ✅ |
| 5 | Leaflet.js map + OSRM real route polyline | ✅ |
| 6 | DeepLabV3 deep learning segmentation (optional) | ✅ |
| 7 | Claude AI assistant with multi-turn history | ✅ |
| 8 | Deployment files + final docs | ✅ |
