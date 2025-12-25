from django.db import models
from members.models import Member


class MatchSession(models.Model):
    """대진표 세션 모델"""
    
    date = models.DateField(verbose_name='날짜')
    title = models.CharField(max_length=200, blank=True, verbose_name='제목')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = '대진표 세션'
        verbose_name_plural = '대진표 세션들'
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.date} 대진표"


class Participant(models.Model):
    """대진 참가자 모델 (멤버 또는 게스트)"""
    
    TIMING_CHOICES = [
        ('full', '전체 참석'),
        ('late', '늦게 참석'),
        ('early', '일찍 퇴장'),
        ('partial', '부분 참석'),
    ]
    
    session = models.ForeignKey(MatchSession, on_delete=models.CASCADE, related_name='participants')
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='participations')
    
    # 게스트인 경우 사용
    guest_name = models.CharField(max_length=50, blank=True, verbose_name='게스트 이름')
    guest_gender = models.CharField(max_length=1, blank=True, verbose_name='게스트 성별')
    guest_ntrp = models.CharField(max_length=3, blank=True, default='2.5', verbose_name='게스트 NTRP')
    
    # 참석 시간 설정
    timing = models.CharField(max_length=10, choices=TIMING_CHOICES, default='full', verbose_name='참석 유형')
    start_round = models.PositiveIntegerField(default=1, verbose_name='시작 라운드')
    end_round = models.PositiveIntegerField(default=99, verbose_name='종료 라운드')
    
    class Meta:
        verbose_name = '참가자'
        verbose_name_plural = '참가자들'
    
    def __str__(self):
        return self.display_name
    
    @property
    def display_name(self):
        if self.member:
            return self.member.name
        return self.guest_name or '게스트'
    
    @property
    def ntrp(self):
        if self.member:
            return self.member.ntrp
        return self.guest_ntrp
    
    @property
    def gender(self):
        if self.member:
            return self.member.gender
        return self.guest_gender
    
    def is_available_for_round(self, round_num):
        """해당 라운드에 참가 가능한지 확인"""
        return self.start_round <= round_num <= self.end_round


class Match(models.Model):
    """개별 경기 모델"""
    
    session = models.ForeignKey(MatchSession, on_delete=models.CASCADE, related_name='matches')
    round_number = models.PositiveIntegerField(verbose_name='라운드')
    court_number = models.PositiveIntegerField(verbose_name='코트 번호')
    
    # 팀 A
    team_a_player1 = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='matches_as_a1', null=True, blank=True)
    team_a_player2 = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='matches_as_a2', null=True, blank=True)
    
    # 팀 B
    team_b_player1 = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='matches_as_b1', null=True, blank=True)
    team_b_player2 = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='matches_as_b2', null=True, blank=True)
    
    class Meta:
        verbose_name = '경기'
        verbose_name_plural = '경기들'
        ordering = ['round_number', 'court_number']
    
    def __str__(self):
        return f"R{self.round_number} 코트{self.court_number}"
    
    @property
    def team_a_names(self):
        names = []
        if self.team_a_player1:
            names.append(self.team_a_player1.display_name)
        if self.team_a_player2:
            names.append(self.team_a_player2.display_name)
        return ' & '.join(names)
    
    @property
    def team_b_names(self):
        names = []
        if self.team_b_player1:
            names.append(self.team_b_player1.display_name)
        if self.team_b_player2:
            names.append(self.team_b_player2.display_name)
        return ' & '.join(names)

