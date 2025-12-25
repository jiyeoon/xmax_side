from django.contrib import admin
from .models import MatchSession, Participant, Match


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0


class MatchInline(admin.TabularInline):
    model = Match
    extra = 0


@admin.register(MatchSession)
class MatchSessionAdmin(admin.ModelAdmin):
    list_display = ['date', 'title', 'created_at']
    list_filter = ['date']
    inlines = [ParticipantInline, MatchInline]


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'session', 'timing', 'start_round', 'end_round']
    list_filter = ['session', 'timing']


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['session', 'round_number', 'court_number', 'team_a_names', 'team_b_names']
    list_filter = ['session', 'round_number']

