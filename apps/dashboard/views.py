import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import City, AnalysisResult
from config.settings_config import CITIES

import sys
import os

import logging
logger = logging.getLogger(__name__)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def home(request):
    """Landing page with city selector and route input form."""
    # Auto-populate cities from config if DB is empty
    _ensure_cities_exist()

    cities = City.objects.all().order_by('display_name')
    recent_analyses = AnalysisResult.objects.select_related('city').order_by('-created_at')[:5]

    context = {
        'cities': cities,
        'recent_analyses': recent_analyses,
        'page_title': 'GeoComfortIQ — Urban Outdoor Comfort Analysis',
    }
    return render(request, 'home/index.html', context)


def analyze(request):
    """Process form submission, run analysis pipeline, redirect to dashboard."""
    if request.method != 'POST':
        return redirect('dashboard:home')

    city_slug = request.POST.get('city', '').strip()
    start_location = request.POST.get('start_location', '').strip()
    end_location = request.POST.get('end_location', '').strip()

    if not all([city_slug, start_location, end_location]):
        return redirect('dashboard:home')

    city = get_object_or_404(City, slug=city_slug)

    # ── Check cache: same city + route within last hour ──────────────────────
    one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    cached = AnalysisResult.objects.filter(
        city=city,
        start_location__iexact=start_location,
        end_location__iexact=end_location,
        created_at__gte=one_hour_ago,
    ).first()

    if cached:
        cached.is_cached = True
        cached.save(update_fields=['is_cached'])
        return redirect('dashboard:dashboard_detail', result_id=cached.id)

    # ── Run full analysis pipeline ────────────────────────────────────────────
    result = _run_analysis_pipeline(city, start_location, end_location)
    return redirect('dashboard:dashboard_detail', result_id=result.id)


def dashboard_detail(request, result_id):
    """Main dashboard view showing full analysis result."""
    from services.weather_service import fetch_weather_aqi, travel_advice
    result = get_object_or_404(AnalysisResult, id=result_id)
    cities = City.objects.all().order_by('display_name')
    chart_data = result.to_chart_data()

    # Use start location coords for weather (more accurate than city centre)
    # Fall back to city centre if start coords not available
    weather_lat = result.start_lat if result.start_lat else result.city.latitude
    weather_lon = result.start_lon if result.start_lon else result.city.longitude
    weather = fetch_weather_aqi(weather_lat, weather_lon, result.city.display_name)
    weather['travel_advice'] = travel_advice(weather)

    # Phase 5: fetch real route from OSRM
    from services.route_service import get_route
    route = get_route(
        result.start_lat, result.start_lon,
        result.end_lat,   result.end_lon,
    )

    context = {
        'result': result,
        'cities': cities,
        'weather': weather,
        'route': route,
        'route_json': json.dumps(route),
        'dl_available': result.dl_available,
        'image_used':        result.image_used,
        'image_available':   result.image_available,
        'chart_data_json': json.dumps(chart_data),
        'page_title': f'Dashboard — {result.city.display_name}',
    }
    return render(request, 'dashboard/detail.html', context)


def api_localities(request):
    """
    Returns locality suggestions for autocomplete.
    Query param: q=jank&city=lucknow
    """
    from services.geocoder import LOCALITY_DB
    q    = request.GET.get('q', '').strip().lower()
    city = request.GET.get('city', '').strip().lower()

    if len(q) < 2:
        return JsonResponse({'suggestions': []})

    results = []
    for name, (lat, lon) in LOCALITY_DB.items():
        # Filter by city if provided (skip generic city-centre entries)
        if city and city not in name and name not in city:
            # Only include if name could plausibly be in that city
            # Skip city-centre entries for other cities
            pass
        if q in name:
            results.append({
                'name':  name.title(),
                'lat':   lat,
                'lon':   lon,
            })
        if len(results) >= 8:
            break

    return JsonResponse({'suggestions': results})


def api_cities(request):
    """JSON endpoint: list all cities."""
    cities = list(City.objects.values('slug', 'display_name', 'state', 'latitude', 'longitude'))
    return JsonResponse({'cities': cities})


def api_result_json(request, result_id):
    """JSON endpoint: full result data (for AJAX refresh)."""
    result = get_object_or_404(AnalysisResult, id=result_id)
    data = {
        'id': result.id,
        'city': result.city.display_name,
        'start': result.start_location,
        'end': result.end_location,
        'green_pct': result.green_pct,
        'dust_pct': result.dust_pct,
        'builtup_pct': result.builtup_pct,
        'shade_pct': result.shade_pct,
        'congestion_pct': result.congestion_pct,
        'water_pct': result.water_pct,
        'comfort_score': result.comfort_score,
        'risk_category': result.risk_category,
        'aqi': result.aqi,
        'temperature': result.temperature,
        'humidity': result.humidity,
        'chart_data': result.to_chart_data(),
    }
    return JsonResponse(data)


# ─── Internal Helpers ──────────────────────────────────────────────────────────

def _ensure_cities_exist():
    """Seed City table from config if empty."""
    if City.objects.exists():
        return
    for slug, info in CITIES.items():
        City.objects.get_or_create(
            slug=slug,
            defaults={
                'display_name': info['display'],
                'state': info['state'],
                'latitude': info['lat'],
                'longitude': info['lon'],
                'satellite_image': info.get('image', ''),
            }
        )


def _run_analysis_pipeline(city, start_location, end_location):
    """
    Phase 1: Returns a stub result with placeholder values.
    Phase 2+ will replace with real OpenCV analysis.
    """
    from services.geocoder import geocode_location
    from services.comfort_score import classify_and_score
    from services.weather_service import fetch_weather_aqi

    # Geocode start + end
    start_coords = geocode_location(start_location, city.display_name)
    end_coords = geocode_location(end_location, city.display_name)

    # Parameter extraction — uses OpenCV if satellite image exists, else mock
    from apps.analysis.analyzer import analyze_city_image
    params = analyze_city_image(city.slug, city.satellite_image or f"{city.slug}.jpg")

    # Log what image source was used (visible in terminal)
    logger.info(f"Analysis source for {city.slug}: {params.get('source','?')} | dl={params.get('dl_available',False)}")

    # Phase 3: KMeans + comfort score in one call
    result_data = classify_and_score(params)
    score = result_data['comfort_score']
    risk  = result_data['risk_category']

    # Live weather/AQI
    env_data = fetch_weather_aqi(city.latitude, city.longitude, city.display_name)

    result = AnalysisResult.objects.create(
        city=city,
        start_location=start_location,
        end_location=end_location,
        start_lat=start_coords.get('lat'),
        start_lon=start_coords.get('lon'),
        end_lat=end_coords.get('lat'),
        end_lon=end_coords.get('lon'),
        green_pct=params['green_pct'],
        dust_pct=params['dust_pct'],
        builtup_pct=params['builtup_pct'],
        shade_pct=params['shade_pct'],
        congestion_pct=params['congestion_pct'],
        water_pct=params['water_pct'],
        comfort_score=score,
        risk_category=risk,
        aqi=env_data.get('aqi'),
        pm25=env_data.get('pm25'),
        pm10=env_data.get('pm10'),
        temperature=env_data.get('temperature'),
        humidity=env_data.get('humidity'),
        dl_available=params.get('dl_available', False),
        image_used=params.get('image_used', None),
        image_available=params.get('image_available', False),
    )
    return result



