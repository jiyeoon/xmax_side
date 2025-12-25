from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'start_time', 'end_time', 'location']
    list_filter = ['date']
    search_fields = ['title', 'location']
    filter_horizontal = ['attendees']
    ordering = ['-date', 'start_time']

