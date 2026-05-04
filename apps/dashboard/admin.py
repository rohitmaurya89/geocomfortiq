from django.contrib import admin
from .models import City, AnalysisResult


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'state', 'latitude', 'longitude']
    search_fields = ['display_name', 'state']
    prepopulated_fields = {'slug': ('display_name',)}


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ['city', 'start_location', 'end_location', 'comfort_score', 'risk_category', 'created_at']
    list_filter = ['risk_category', 'city', 'created_at']
    search_fields = ['start_location', 'end_location']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
