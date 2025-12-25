from django.db import models


class Member(models.Model):
    """테니스 클럽 멤버 모델"""
    
    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
    ]
    
    STATUS_CHOICES = [
        ('active', '활동중'),
        ('inactive', '휴회중'),
    ]
    
    NTRP_CHOICES = [
        ('1.0', '1.0'),
        ('1.5', '1.5'),
        ('2.0', '2.0'),
        ('2.5', '2.5'),
        ('3.0', '3.0'),
        ('3.5', '3.5'),
        ('4.0', '4.0'),
        ('4.5', '4.5'),
        ('5.0', '5.0'),
        ('5.5', '5.5'),
        ('6.0', '6.0'),
        ('6.5', '6.5'),
        ('7.0', '7.0'),
    ]
    
    name = models.CharField(max_length=50, verbose_name='이름')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='성별')
    experience_years = models.PositiveIntegerField(default=0, verbose_name='구력(년)')
    ntrp = models.CharField(max_length=3, choices=NTRP_CHOICES, default='2.5', verbose_name='NTRP')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name='상태')
    phone = models.CharField(max_length=20, blank=True, verbose_name='연락처')
    is_admin = models.BooleanField(default=False, verbose_name='운영진')
    joined_date = models.DateField(auto_now_add=True, verbose_name='가입일')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '멤버'
        verbose_name_plural = '멤버들'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def display_info(self):
        return f"{self.name} | {self.get_gender_display()} | 구력 {self.experience_years}년 | NTRP {self.ntrp}"

