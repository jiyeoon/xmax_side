# 🎾 Tennis Club Manager

테니스 클럽 운영을 위한 커뮤니티 웹사이트입니다. Django로 개발되었으며, 심플하고 귀여운 디자인으로 멤버 관리, 일정 관리, 대진표 자동 생성 기능을 제공합니다.

![Tennis Club](https://img.shields.io/badge/Tennis-Club-2DD4BF?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjEwIi8+PC9zdmc+)

## ✨ 주요 기능

### 1. 📅 일정 관리
- 월별 캘린더 뷰로 클럽 일정 확인
- 일정 등록 (날짜, 시간, 장소, 참석자)
- 구글 캘린더 연동 지원 (선택적)

### 2. 🏸 대진표 생성
- 참석 멤버 선택 및 게스트 추가
- **늦게 참석 / 일찍 퇴장** 옵션 지원
- NTRP 기반 밸런스 있는 자동 대진 생성
- 버튼 클릭으로 새로운 대진표 재생성 (시간 제약 유지)
- 코트 수, 라운드 수 설정 가능

### 3. 👥 멤버 관리
- 멤버 추가, 수정, 삭제
- 활동중 / 휴회중 상태 관리
- 이름, 성별, 구력, NTRP 정보 관리

## 🚀 시작하기

### 요구 사항
- Python 3.10+
- Django 4.2+

### 설치

```bash
# 1. 저장소 클론
git clone <repository-url>
cd xmax_side

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 데이터베이스 마이그레이션
python manage.py makemigrations
python manage.py migrate

# 5. 관리자 계정 생성 (선택)
python manage.py createsuperuser

# 6. 서버 실행
python manage.py runserver
```

### 접속
- 메인 사이트: http://127.0.0.1:8000/
- 관리자 페이지: http://127.0.0.1:8000/admin/

## 📁 프로젝트 구조

```
xmax_side/
├── tennis_club/          # Django 프로젝트 설정
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── members/              # 멤버 관리 앱
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── schedule/             # 일정 관리 앱
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templatetags/
├── matchmaking/          # 대진표 생성 앱
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── matchmaker.py     # 대진 알고리즘
├── templates/            # HTML 템플릿
│   ├── base.html
│   ├── members/
│   ├── schedule/
│   └── matchmaking/
├── static/               # 정적 파일
│   ├── css/
│   └── js/
├── requirements.txt
└── manage.py
```

## 🎨 디자인

- **색상 팔레트**: 민트 그린 + 코랄 + 크림
- **폰트**: Noto Sans KR + Quicksand
- **특징**: 심플하고 귀여운 UI/UX

## 🔧 대진표 알고리즘

대진표 생성 알고리즘은 다음 요소를 고려합니다:

1. **NTRP 밸런스**: 팀 간 NTRP 합계 차이 최소화
2. **파트너 다양성**: 같은 파트너와 반복 매칭 방지
3. **상대 다양성**: 같은 상대와 반복 대결 방지
4. **게임 수 균형**: 모든 참가자가 비슷한 게임 수 플레이
5. **시간 제약 반영**: 늦게 오거나 일찍 가는 참가자 고려

## 📱 반응형 디자인

- 데스크톱: 전체 사이드바 + 넓은 콘텐츠 영역
- 모바일: 축소된 아이콘 사이드바 + 적응형 레이아웃

## 📄 라이선스

MIT License

---

Made with 🎾 and ❤️ for Tennis Lovers
