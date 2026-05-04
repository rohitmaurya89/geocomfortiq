from django.db import models
from django.utils import timezone


class City(models.Model):
    """Registered cities with satellite data."""
    slug = models.SlugField(unique=True)
    display_name = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    satellite_image = models.CharField(max_length=255, blank=True)  # relative path
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ['display_name']

    def __str__(self):
        return f"{self.display_name}, {self.state}"


class AnalysisResult(models.Model):
    """Stores results of a comfort analysis request."""
    RISK_CHOICES = [
        ('safe', 'Safe'),
        ('moderate', 'Moderate'),
        ('risky', 'Risky'),
    ]

    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='analyses')
    start_location = models.CharField(max_length=255)
    end_location = models.CharField(max_length=255)

    # Geocoded coordinates
    start_lat = models.FloatField(null=True, blank=True)
    start_lon = models.FloatField(null=True, blank=True)
    end_lat = models.FloatField(null=True, blank=True)
    end_lon = models.FloatField(null=True, blank=True)

    # OpenCV extracted parameters (all as % 0–100)
    green_pct = models.FloatField(default=0)
    dust_pct = models.FloatField(default=0)
    builtup_pct = models.FloatField(default=0)
    shade_pct = models.FloatField(default=0)
    congestion_pct = models.FloatField(default=0)
    water_pct = models.FloatField(default=0)

    # Optional spectral indices
    ndvi = models.FloatField(null=True, blank=True)
    ndbi = models.FloatField(null=True, blank=True)

    # Comfort score
    comfort_score = models.FloatField(default=0)
    risk_category = models.CharField(max_length=20, choices=RISK_CHOICES, default='moderate')

    # Live environment data
    aqi = models.FloatField(null=True, blank=True)
    pm25 = models.FloatField(null=True, blank=True)
    pm10 = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    is_cached = models.BooleanField(default=False)
    dl_available = models.BooleanField(default=False)   # Phase 6: was DL used?
    image_used        = models.CharField(max_length=255, blank=True, null=True)
    image_available   = models.BooleanField(default=False)  # True = real satellite data used

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.city} | {self.start_location} → {self.end_location} | Score: {self.comfort_score:.1f}"

    def get_risk_color(self):
        colors = {'safe': '#22c55e', 'moderate': '#f59e0b', 'risky': '#ef4444'}
        return colors.get(self.risk_category, '#6b7280')

    def get_risk_icon(self):
        icons = {'safe': '✅', 'moderate': '⚠️', 'risky': '🚨'}
        return icons.get(self.risk_category, '❓')

    def to_chart_data(self):
        """Returns dict for Chart.js pie/bar charts."""
        return {
            'labels': ['Green Cover', 'Dust/Open Land', 'Built-up', 'Shade', 'Congestion', 'Water'],
            'values': [
                round(self.green_pct, 1),
                round(self.dust_pct, 1),
                round(self.builtup_pct, 1),
                round(self.shade_pct, 1),
                round(self.congestion_pct, 1),
                round(self.water_pct, 1),
            ],
            'colors': ['#22c55e', '#d97706', '#6b7280', '#3b82f6', '#ef4444', '#06b6d4'],
        }
