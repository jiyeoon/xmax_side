from django.db import models
from members.models import Member


class Event(models.Model):
    """클럽 일정 모델"""
    
    RECURRENCE_CHOICES = [
        ('none', '반복 없음'),
        ('daily', '매일'),
        ('weekly', '매주'),
        ('custom', '사용자 정의'),
    ]
    
    WEEKDAY_CHOICES = [
        (0, '월'),
        (1, '화'),
        (2, '수'),
        (3, '목'),
        (4, '금'),
        (5, '토'),
        (6, '일'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='제목')
    date = models.DateField(verbose_name='날짜')
    start_time = models.TimeField(verbose_name='시작 시간')
    end_time = models.TimeField(verbose_name='종료 시간')
    location = models.CharField(max_length=200, verbose_name='장소')
    description = models.TextField(blank=True, verbose_name='설명')
    attendees = models.ManyToManyField(Member, blank=True, related_name='events', verbose_name='참석 멤버')
    google_event_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='구글 캘린더 ID')
    
    # 반복 일정 관련 필드
    recurrence_type = models.CharField(
        max_length=10, 
        choices=RECURRENCE_CHOICES, 
        default='none', 
        verbose_name='반복 유형'
    )
    recurrence_end_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name='반복 종료일'
    )
    recurrence_parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='recurrence_children',
        verbose_name='원본 일정'
    )
    # 사용자 정의 반복 시 특정 요일들 (JSON으로 저장: [0,2,4] = 월,수,금)
    recurrence_weekdays = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name='반복 요일'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '일정'
        verbose_name_plural = '일정들'
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.title} ({self.date})"
    
    @property
    def time_range(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
    
    @property
    def is_recurring(self):
        """반복 일정인지 확인"""
        return self.recurrence_type != 'none' or self.recurrence_parent is not None
    
    @property
    def is_parent_event(self):
        """반복 일정의 원본인지 확인"""
        return self.recurrence_type != 'none' and self.recurrence_parent is None
    
    def get_recurrence_weekdays_list(self):
        """반복 요일 리스트 반환"""
        if self.recurrence_weekdays:
            import json
            try:
                return json.loads(self.recurrence_weekdays)
            except:
                return []
        return []
