from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Count
from datetime import datetime, timedelta
from .models import Member
from schedule.models import Event
import json


def member_list(request):
    """멤버 목록 페이지"""
    active_members = Member.objects.filter(status='active')
    inactive_members = Member.objects.filter(status='inactive')
    
    context = {
        'active_members': active_members,
        'inactive_members': inactive_members,
        'ntrp_choices': Member.NTRP_CHOICES,
        'gender_choices': Member.GENDER_CHOICES,
        'status_choices': Member.STATUS_CHOICES,
    }
    return render(request, 'members/member_list.html', context)


@require_http_methods(["POST"])
def member_create(request):
    """멤버 생성 API"""
    try:
        data = json.loads(request.body)
        member = Member.objects.create(
            name=data.get('name'),
            gender=data.get('gender'),
            experience_years=int(data.get('experience_years', 0)),
            ntrp=data.get('ntrp', '2.5'),
            status=data.get('status', 'active'),
            phone=data.get('phone', ''),
            is_admin=data.get('is_admin', False),
        )
        return JsonResponse({
            'success': True,
            'member': {
                'id': member.id,
                'name': member.name,
                'gender': member.gender,
                'gender_display': member.get_gender_display(),
                'experience_years': member.experience_years,
                'ntrp': member.ntrp,
                'status': member.status,
                'status_display': member.get_status_display(),
                'phone': member.phone,
                'is_admin': member.is_admin,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def member_update(request, member_id):
    """멤버 수정 API"""
    try:
        member = get_object_or_404(Member, id=member_id)
        data = json.loads(request.body)
        
        member.name = data.get('name', member.name)
        member.gender = data.get('gender', member.gender)
        member.experience_years = int(data.get('experience_years', member.experience_years))
        member.ntrp = data.get('ntrp', member.ntrp)
        member.status = data.get('status', member.status)
        member.phone = data.get('phone', member.phone)
        if 'is_admin' in data:
            member.is_admin = data.get('is_admin', False)
        member.save()
        
        return JsonResponse({
            'success': True,
            'member': {
                'id': member.id,
                'name': member.name,
                'gender': member.gender,
                'gender_display': member.get_gender_display(),
                'experience_years': member.experience_years,
                'ntrp': member.ntrp,
                'status': member.status,
                'status_display': member.get_status_display(),
                'phone': member.phone,
                'is_admin': member.is_admin,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def member_delete(request, member_id):
    """멤버 삭제 API"""
    try:
        member = get_object_or_404(Member, id=member_id)
        member.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def member_api_list(request):
    """멤버 목록 API (JSON)"""
    members = Member.objects.filter(status='active').values(
        'id', 'name', 'gender', 'experience_years', 'ntrp', 'status'
    )
    return JsonResponse({'members': list(members)})


def member_detail(request, member_id):
    """멤버 상세 정보 API (참석률 통계 포함)"""
    member = get_object_or_404(Member, id=member_id)
    today = timezone.now().date()
    
    # 전체 일정 (과거 일정만)
    all_past_events = Event.objects.filter(date__lte=today)
    total_events = all_past_events.count()
    
    # 참석한 일정
    attended_events = all_past_events.filter(attendees=member)
    attended_count = attended_events.count()
    
    # 참석률 계산
    attendance_rate = round((attended_count / total_events * 100), 1) if total_events > 0 else 0
    
    # 최근 3개월 월별 참석률
    monthly_stats = []
    for i in range(3):
        month_date = today - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)
        
        month_events = Event.objects.filter(date__gte=month_start, date__lte=min(month_end, today))
        month_total = month_events.count()
        month_attended = month_events.filter(attendees=member).count()
        month_rate = round((month_attended / month_total * 100), 1) if month_total > 0 else 0
        
        monthly_stats.append({
            'month': f"{month_date.year}년 {month_date.month}월",
            'total': month_total,
            'attended': month_attended,
            'rate': month_rate,
        })
    
    # 최근 참석한 일정 (최근 5개)
    recent_attended = attended_events.order_by('-date')[:5]
    recent_events_list = [
        {
            'id': e.id,
            'title': e.title,
            'date': e.date.strftime('%Y-%m-%d'),
            'location': e.location,
        }
        for e in recent_attended
    ]
    
    # 연속 참석 기록
    consecutive_count = 0
    past_events_ordered = all_past_events.order_by('-date')
    for event in past_events_ordered:
        if member in event.attendees.all():
            consecutive_count += 1
        else:
            break
    
    return JsonResponse({
        'id': member.id,
        'name': member.name,
        'gender': member.gender,
        'gender_display': member.get_gender_display(),
        'experience_years': member.experience_years,
        'ntrp': member.ntrp,
        'status': member.status,
        'status_display': member.get_status_display(),
        'phone': member.phone,
        'stats': {
            'total_events': total_events,
            'attended_count': attended_count,
            'attendance_rate': attendance_rate,
            'consecutive_count': consecutive_count,
            'monthly_stats': monthly_stats,
            'recent_events': recent_events_list,
        }
    })

