from django.contrib import admin
from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'gender', 'experience_years', 'ntrp', 'status', 'joined_date']
    list_filter = ['status', 'gender', 'ntrp']
    search_fields = ['name', 'phone']
    ordering = ['name']

