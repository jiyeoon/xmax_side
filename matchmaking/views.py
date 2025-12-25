from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import MatchSession, Participant, Match
from .matchmaker import generate_match_schedule
from members.models import Member
import json


def get_match_type(team_a, team_b):
    """
    매치 타입 결정 (남복/여복/혼복/잡복)
    
    올바른 복식 규칙:
    - 남복: (남남) vs (남남) → 남자 4명, 여자 0명
    - 여복: (여여) vs (여여) → 여자 4명, 남자 0명
    - 혼복: (남여) vs (남여) → 남자 2명, 여자 2명
    - 잡복: 그 외 조합 (정식 복식이 불가능할 때)
    """
    genders = []
    for p in team_a + team_b:
        genders.append(p.gender)
    
    male_count = genders.count('M')
    female_count = genders.count('F')
    
    if male_count == 4 and female_count == 0:
        return {'type': 'male', 'label': '남복', 'emoji': '👬'}
    elif male_count == 0 and female_count == 4:
        return {'type': 'female', 'label': '여복', 'emoji': '👭'}
    elif male_count == 2 and female_count == 2:
        return {'type': 'mixed', 'label': '혼복', 'emoji': '👫'}
    else:
        # 잡복 (정식 복식이 불가능한 조합)
        return {'type': 'any', 'label': '잡복', 'emoji': '🎾'}


def matchmaking_page(request):
    """대진표 생성 페이지"""
    members = Member.objects.filter(status='active').order_by('name')
    recent_sessions = MatchSession.objects.all()[:10]
    
    context = {
        'members': members,
        'recent_sessions': recent_sessions,
        'timing_choices': Participant.TIMING_CHOICES,
        'ntrp_choices': Member.NTRP_CHOICES,
        'gender_choices': Member.GENDER_CHOICES,
    }
    return render(request, 'matchmaking/matchmaking.html', context)


@require_http_methods(["POST"])
def generate_matches(request):
    """대진표 생성 API"""
    try:
        data = json.loads(request.body)
        
        # 세션 생성 (기존 세션 사용 또는 새로 생성)
        session_id = data.get('session_id')
        if session_id:
            session = get_object_or_404(MatchSession, id=session_id)
            # 기존 매치 삭제 (재생성)
            session.matches.all().delete()
        else:
            session = MatchSession.objects.create(
                date=data.get('date', timezone.now().date()),
                title=data.get('title', ''),
            )
            
            # 참가자 생성
            for p_data in data.get('participants', []):
                participant = Participant(session=session)
                
                if p_data.get('member_id'):
                    participant.member_id = p_data['member_id']
                else:
                    participant.guest_name = p_data.get('name', '게스트')
                    participant.guest_gender = p_data.get('gender', 'M')
                    participant.guest_ntrp = p_data.get('ntrp', '2.5')
                
                participant.timing = p_data.get('timing', 'full')
                participant.start_round = p_data.get('start_round', 1)
                participant.end_round = p_data.get('end_round', 99)
                participant.save()
        
        # 대진표 생성
        participants = list(session.participants.all())
        num_courts = data.get('num_courts', 2)
        num_rounds = data.get('num_rounds', 6)
        
        schedule = generate_match_schedule(participants, num_courts, num_rounds)
        
        # 매치 저장
        for round_data in schedule:
            for match_data in round_data['matches']:
                Match.objects.create(
                    session=session,
                    round_number=match_data['round'],
                    court_number=match_data['court'],
                    team_a_player1=match_data['team_a'][0] if len(match_data['team_a']) > 0 else None,
                    team_a_player2=match_data['team_a'][1] if len(match_data['team_a']) > 1 else None,
                    team_b_player1=match_data['team_b'][0] if len(match_data['team_b']) > 0 else None,
                    team_b_player2=match_data['team_b'][1] if len(match_data['team_b']) > 1 else None,
                )
        
        # 응답 데이터 생성
        response_schedule = []
        for round_data in schedule:
            round_info = {
                'round': round_data['round'],
                'matches': [],
                'resting': [p.display_name for p in round_data['resting']],
            }
            for match_data in round_data['matches']:
                match_type = get_match_type(list(match_data['team_a']), list(match_data['team_b']))
                round_info['matches'].append({
                    'court': match_data['court'],
                    'team_a': [p.display_name for p in match_data['team_a']],
                    'team_a_ntrp': [p.ntrp for p in match_data['team_a']],
                    'team_a_gender': [p.gender for p in match_data['team_a']],
                    'team_b': [p.display_name for p in match_data['team_b']],
                    'team_b_ntrp': [p.ntrp for p in match_data['team_b']],
                    'team_b_gender': [p.gender for p in match_data['team_b']],
                    'match_type': match_type,
                })
            response_schedule.append(round_info)
        
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'schedule': response_schedule,
        })
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=400)


@require_http_methods(["POST"])
def regenerate_matches(request):
    """대진표 재생성 API (시간 제약 유지)"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({'success': False, 'error': '세션 ID가 필요합니다.'}, status=400)
        
        session = get_object_or_404(MatchSession, id=session_id)
        
        # 기존 매치 삭제
        session.matches.all().delete()
        
        # 대진표 재생성
        participants = list(session.participants.all())
        num_courts = data.get('num_courts', 2)
        num_rounds = data.get('num_rounds', 6)
        
        schedule = generate_match_schedule(participants, num_courts, num_rounds)
        
        # 매치 저장
        for round_data in schedule:
            for match_data in round_data['matches']:
                Match.objects.create(
                    session=session,
                    round_number=match_data['round'],
                    court_number=match_data['court'],
                    team_a_player1=match_data['team_a'][0] if len(match_data['team_a']) > 0 else None,
                    team_a_player2=match_data['team_a'][1] if len(match_data['team_a']) > 1 else None,
                    team_b_player1=match_data['team_b'][0] if len(match_data['team_b']) > 0 else None,
                    team_b_player2=match_data['team_b'][1] if len(match_data['team_b']) > 1 else None,
                )
        
        # 응답 데이터 생성
        response_schedule = []
        for round_data in schedule:
            round_info = {
                'round': round_data['round'],
                'matches': [],
                'resting': [p.display_name for p in round_data['resting']],
            }
            for match_data in round_data['matches']:
                match_type = get_match_type(list(match_data['team_a']), list(match_data['team_b']))
                round_info['matches'].append({
                    'court': match_data['court'],
                    'team_a': [p.display_name for p in match_data['team_a']],
                    'team_a_ntrp': [p.ntrp for p in match_data['team_a']],
                    'team_a_gender': [p.gender for p in match_data['team_a']],
                    'team_b': [p.display_name for p in match_data['team_b']],
                    'team_b_ntrp': [p.ntrp for p in match_data['team_b']],
                    'team_b_gender': [p.gender for p in match_data['team_b']],
                    'match_type': match_type,
                })
            response_schedule.append(round_info)
        
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'schedule': response_schedule,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def session_detail(request, session_id):
    """세션 상세 정보 API"""
    session = get_object_or_404(MatchSession, id=session_id)
    matches = session.matches.all().order_by('round_number', 'court_number')
    participants = session.participants.all()
    
    # 라운드별로 그룹화
    rounds = {}
    for match in matches:
        if match.round_number not in rounds:
            rounds[match.round_number] = []
        rounds[match.round_number].append({
            'court': match.court_number,
            'team_a': match.team_a_names,
            'team_b': match.team_b_names,
        })
    
    return JsonResponse({
        'session_id': session.id,
        'date': session.date.strftime('%Y-%m-%d'),
        'title': session.title,
        'participants': [
            {
                'name': p.display_name,
                'timing': p.get_timing_display(),
                'start_round': p.start_round,
                'end_round': p.end_round,
            }
            for p in participants
        ],
        'rounds': rounds,
    })

