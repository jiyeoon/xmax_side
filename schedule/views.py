from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .models import Event
from members.models import Member
import json
import calendar


def home(request):
    """홈 대시보드 페이지"""
    today = datetime.now().date()
    
    # 다가오는 일정 (오늘 이후 3개)
    upcoming_events = Event.objects.filter(
        date__gte=today
    ).prefetch_related('attendees').order_by('date', 'start_time')[:3]
    
    # 가장 가까운 일정
    next_event = upcoming_events.first() if upcoming_events else None
    
    # 이번 달 일정 수
    this_month_events = Event.objects.filter(
        date__year=today.year,
        date__month=today.month
    ).count()
    
    # 멤버 현황
    total_members = Member.objects.filter(status='active').count()
    male_members = Member.objects.filter(status='active', gender='M').count()
    female_members = Member.objects.filter(status='active', gender='F').count()
    
    # 다음 일정 참석자 수
    next_event_attendees = next_event.attendees.count() if next_event else 0
    
    context = {
        'today': today,
        'upcoming_events': upcoming_events,
        'next_event': next_event,
        'next_event_attendees': next_event_attendees,
        'this_month_events': this_month_events,
        'total_members': total_members,
        'male_members': male_members,
        'female_members': female_members,
    }
    return render(request, 'home.html', context)


def schedule_calendar(request):
    """일정 캘린더 페이지"""
    today = datetime.now()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    # 이전/다음 달 계산
    current_date = datetime(year, month, 1)
    prev_month = current_date - relativedelta(months=1)
    next_month = current_date + relativedelta(months=1)
    
    # 해당 월의 일정 가져오기
    events = Event.objects.filter(
        date__year=year,
        date__month=month
    ).prefetch_related('attendees')
    
    # 캘린더 데이터 생성
    cal = calendar.Calendar(firstweekday=6)  # 일요일 시작
    month_days = cal.monthdatescalendar(year, month)
    
    # 일정을 날짜별로 그룹화
    events_by_date = {}
    for event in events:
        date_str = event.date.strftime('%Y-%m-%d')
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append(event)
    
    context = {
        'year': year,
        'month': month,
        'month_name': current_date.strftime('%Y년 %m월'),
        'prev_year': prev_month.year,
        'prev_month': prev_month.month,
        'next_year': next_month.year,
        'next_month': next_month.month,
        'month_days': month_days,
        'events_by_date': events_by_date,
        'today': today.date(),
        'members': Member.objects.filter(status='active'),
    }
    return render(request, 'schedule/calendar.html', context)


def event_detail(request, event_id):
    """일정 상세 API"""
    event = get_object_or_404(Event, id=event_id)
    attendees = list(event.attendees.values('id', 'name', 'gender'))
    
    return JsonResponse({
        'id': event.id,
        'title': event.title,
        'date': event.date.strftime('%Y-%m-%d'),
        'start_time': event.start_time.strftime('%H:%M'),
        'end_time': event.end_time.strftime('%H:%M'),
        'location': event.location,
        'description': event.description,
        'attendees': attendees,
        'recurrence_type': event.recurrence_type,
        'recurrence_end_date': event.recurrence_end_date.strftime('%Y-%m-%d') if event.recurrence_end_date else None,
        'recurrence_weekdays': event.get_recurrence_weekdays_list(),
        'is_recurring': event.is_recurring,
        'is_parent_event': event.is_parent_event,
        'recurrence_parent_id': event.recurrence_parent_id,
    })


@require_http_methods(["POST"])
def event_create(request):
    """일정 생성 API (반복 일정 지원)"""
    try:
        data = json.loads(request.body)
        
        # 기본 일정 데이터
        title = data.get('title', '').strip()
        
        # 제목 유효성 검사
        if not title:
            return JsonResponse({'success': False, 'error': '제목을 입력해주세요.'}, status=400)
        start_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        location = data.get('location')
        description = data.get('description', '')
        attendee_ids = data.get('attendees', [])
        
        # 반복 설정
        recurrence_type = data.get('recurrence_type', 'none')
        recurrence_end_date_str = data.get('recurrence_end_date')
        recurrence_weekdays = data.get('recurrence_weekdays', [])
        
        # 반복 종료일 파싱
        recurrence_end_date = None
        if recurrence_end_date_str and recurrence_end_date_str.strip():
            recurrence_end_date = datetime.strptime(recurrence_end_date_str, '%Y-%m-%d').date()
        elif recurrence_type != 'none':
            # 반복 종료일이 없으면 기본 3개월 후로 설정
            recurrence_end_date = start_date + timedelta(days=90)
        
        created_events = []
        
        if recurrence_type == 'none':
            # 단일 일정 생성
            event = Event.objects.create(
                title=title,
                date=start_date,
                start_time=start_time,
                end_time=end_time,
                location=location,
                description=description,
                recurrence_type='none',
            )
            if attendee_ids:
                event.attendees.set(attendee_ids)
            created_events.append(event)
        else:
            # 반복 일정 생성
            # 원본 일정 생성
            parent_event = Event.objects.create(
                title=title,
                date=start_date,
                start_time=start_time,
                end_time=end_time,
                location=location,
                description=description,
                recurrence_type=recurrence_type,
                recurrence_end_date=recurrence_end_date,
                recurrence_weekdays=json.dumps(recurrence_weekdays) if recurrence_weekdays else '',
            )
            if attendee_ids:
                parent_event.attendees.set(attendee_ids)
            created_events.append(parent_event)
            
            # 반복 일정 생성 (자식 이벤트들)
            current_date = start_date
            max_events = 365  # 최대 1년치
            event_count = 0
            
            while event_count < max_events:
                # 다음 날짜 계산
                if recurrence_type == 'daily':
                    current_date += timedelta(days=1)
                elif recurrence_type == 'weekly':
                    current_date += timedelta(weeks=1)
                elif recurrence_type == 'custom':
                    current_date += timedelta(days=1)
                    # 선택된 요일이 아니면 건너뛰기
                    while current_date <= recurrence_end_date and current_date.weekday() not in recurrence_weekdays:
                        current_date += timedelta(days=1)
                
                # 종료일 체크
                if current_date > recurrence_end_date:
                    break
                
                # 자식 이벤트 생성
                child_event = Event.objects.create(
                    title=title,
                    date=current_date,
                    start_time=start_time,
                    end_time=end_time,
                    location=location,
                    description=description,
                    recurrence_type='none',
                    recurrence_parent=parent_event,
                )
                if attendee_ids:
                    child_event.attendees.set(attendee_ids)
                created_events.append(child_event)
                event_count += 1
        
        return JsonResponse({
            'success': True,
            'event': {
                'id': created_events[0].id,
                'title': created_events[0].title,
                'date': created_events[0].date.strftime('%Y-%m-%d'),
            },
            'created_count': len(created_events),
        })
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False, 
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=400)


@require_http_methods(["POST"])
def event_update(request, event_id):
    """일정 수정 API"""
    try:
        event = get_object_or_404(Event, id=event_id)
        data = json.loads(request.body)
        
        event.title = data.get('title', event.title)
        event.date = data.get('date', event.date)
        event.start_time = data.get('start_time', event.start_time)
        event.end_time = data.get('end_time', event.end_time)
        event.location = data.get('location', event.location)
        event.description = data.get('description', event.description)
        event.save()
        
        # 참석자 업데이트
        if 'attendees' in data:
            event.attendees.set(data['attendees'])
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def event_delete(request, event_id):
    """일정 삭제 API (반복 일정 삭제 옵션 지원)"""
    try:
        event = get_object_or_404(Event, id=event_id)
        data = json.loads(request.body) if request.body else {}
        delete_type = data.get('delete_type', 'single')  # 'single', 'future', 'all'
        
        deleted_count = 0
        
        if not event.is_recurring:
            # 단일 일정 삭제
            event.delete()
            deleted_count = 1
        else:
            if delete_type == 'single':
                # 이번 일정만 삭제
                event.delete()
                deleted_count = 1
            elif delete_type == 'future':
                # 이번 일정 및 앞으로의 모든 일정 삭제
                if event.is_parent_event:
                    # 원본 일정인 경우: 원본 + 이 날짜 이후의 자식들 삭제
                    future_events = Event.objects.filter(
                        recurrence_parent=event,
                        date__gte=event.date
                    )
                    deleted_count = future_events.count() + 1
                    future_events.delete()
                    event.delete()
                else:
                    # 자식 일정인 경우: 이 날짜 이후의 같은 부모 자식들 삭제
                    parent = event.recurrence_parent
                    future_events = Event.objects.filter(
                        recurrence_parent=parent,
                        date__gte=event.date
                    )
                    deleted_count = future_events.count()
                    future_events.delete()
            elif delete_type == 'all':
                # 모든 반복 일정 삭제
                if event.is_parent_event:
                    # 원본 일정인 경우: 원본 + 모든 자식들 삭제
                    children = Event.objects.filter(recurrence_parent=event)
                    deleted_count = children.count() + 1
                    children.delete()
                    event.delete()
                else:
                    # 자식 일정인 경우: 부모 + 모든 형제 삭제
                    parent = event.recurrence_parent
                    if parent:
                        siblings = Event.objects.filter(recurrence_parent=parent)
                        deleted_count = siblings.count() + 1
                        siblings.delete()
                        parent.delete()
                    else:
                        event.delete()
                        deleted_count = 1
        
        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def events_api(request):
    """일정 목록 API (FullCalendar 형식)"""
    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))
    
    events = Event.objects.filter(
        date__year=year,
        date__month=month
    ).prefetch_related('attendees')
    
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'date': event.date.strftime('%Y-%m-%d'),
            'start_time': event.start_time.strftime('%H:%M'),
            'end_time': event.end_time.strftime('%H:%M'),
            'location': event.location,
            'attendees_count': event.attendees.count(),
            'is_recurring': event.is_recurring,
        })
    
    return JsonResponse({'events': events_data})
