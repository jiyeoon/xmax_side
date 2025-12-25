"""
HumbleB 테니스 클럽 대진표 생성 알고리즘 v7

=== 우선순위 ===
1. 연속 휴식 방지 - 한 라운드 쉬면 다음 라운드 반드시 참여
2. 게임 수 균등 - 모든 참가자 동일한 게임 수
3. 매치 타입 분배 - 성별 비율에 따른 여복/남복/혼복 배분
4. 늦참/일퇴 반영 - 제한된 참가자 우선 배정
5. 랜덤성 - 매번 새로운 대진 생성

=== 매치 타입 분배 규칙 ===
- 여4남8: 여복2, 남복6, 혼복4 (여자=여복2+혼복2, 남자=남복3+혼복1)
- 여6남6: 여복3, 남복3, 혼복6 (각자 동성복2+혼복2)
- 여8남4: 여복6, 남복2, 혼복4 (여자=여복3+혼복1, 남자=남복2+혼복2)
- 다른 비율은 수학적으로 계산

=== 제약 조건 ===
- 여복: 여자 4명 필요
- 남복: 남자 4명 필요
- 혼복: 남자 2명 + 여자 2명 필요
- 같은 라운드에 동일인 중복 참여 불가
"""
import random
from collections import defaultdict
from itertools import combinations


def get_match_type(players):
    """플레이어 리스트로 매치 타입 결정"""
    genders = [p.gender for p in players]
    male_count = genders.count('M')
    female_count = genders.count('F')
    
    if male_count == 4 and female_count == 0:
        return 'male'
    elif male_count == 0 and female_count == 4:
        return 'female'
    elif male_count == 2 and female_count == 2:
        return 'mixed'
    else:
        return 'any'


class MatchMaker:
    """대진표 생성기 v7"""
    
    def __init__(self, participants, num_courts=2, num_rounds=6):
        self.participants = participants
        self.num_courts = num_courts
        self.num_rounds = num_rounds
        self.total_matches = num_courts * num_rounds
        
        # 성별 분류
        self.males = [p for p in participants if p.gender == 'M']
        self.females = [p for p in participants if p.gender == 'F']
        
        # 추적 데이터
        self.games_played = {p.id: 0 for p in participants}
        self.match_type_count = {p.id: {'male': 0, 'female': 0, 'mixed': 0} for p in participants}
        self.partner_history = defaultdict(set)
        self.opponent_history = defaultdict(set)
        self.last_played_round = {p.id: 0 for p in participants}
        
        # 매치 타입 계획 (가용 인원 고려)
        self.match_plan = self._create_match_plan_considering_availability()
        self.match_plan_original = self.match_plan.copy()
        
        # 라운드별 매치 타입 미리 결정 (랜덤하게!)
        self.round_match_types = self._distribute_match_types_to_rounds()
    
    def _create_match_plan(self):
        """
        매치 타입 분포 계획 (수학적으로 정확하게 계산)
        
        제약 조건:
        - 여자 슬롯: 4*여복 + 2*혼복 = 여자수 × 목표게임수
        - 남자 슬롯: 4*남복 + 2*혼복 = 남자수 × 목표게임수
        - 총 매치: 여복 + 남복 + 혼복 = 총 매치수
        
        우선순위:
        1. 여4남8 유형: 여복 최대화 (여자 전원 여복 참여)
        2. 여8남4 유형: 남복 최대화 (남자 전원 남복 참여)
        3. 균등 유형: 여복/남복 균형
        """
        num_males = len(self.males)
        num_females = len(self.females)
        total_people = num_males + num_females
        
        if total_people == 0:
            return {'male': 0, 'female': 0, 'mixed': 0}
        
        # 남자만 있을 때
        if num_females == 0:
            return {'male': self.total_matches, 'female': 0, 'mixed': 0}
        # 여자만 있을 때
        if num_males == 0:
            return {'male': 0, 'female': self.total_matches, 'mixed': 0}
        
        # 혼복이 불가능한 경우
        if num_females == 1:
            return {'male': self.total_matches, 'female': 0, 'mixed': 0}
        if num_males == 1:
            return {'male': 0, 'female': self.total_matches, 'mixed': 0}
        
        # 가능한 매치 타입 확인
        can_female_doubles = num_females >= 4
        can_male_doubles = num_males >= 4
        
        # 목표 게임수 계산 - 모든 슬롯을 사용하도록!
        total_slots = self.total_matches * 4
        
        # 각 성별에 슬롯을 비율에 맞게 분배 (반올림으로 총합이 total_slots가 되도록)
        female_ratio = num_females / total_people
        female_slots = round(total_slots * female_ratio)
        male_slots = total_slots - female_slots  # 나머지는 남자에게
        
        # 짝수로 맞추기 (혼복을 위해 2의 배수여야 함)
        if female_slots % 2 != 0:
            female_slots += 1
            male_slots -= 1
        
        # 수학적으로 유효한 조합 찾기
        # 4x + 2y = female_slots (여복 x, 혼복 y)
        # 4z + 2y = male_slots (남복 z, 혼복 y)
        # x + y + z = total_matches
        
        best_plan = None
        best_score = float('-inf')  # 점수가 높을수록 좋음
        
        # 여복 수를 변화시키면서 유효한 조합 찾기
        max_female = min(female_slots // 4, self.total_matches) if can_female_doubles else 0
        
        for x in range(max_female + 1):  # 여복 수
            remaining_female_slots = female_slots - 4 * x
            
            # 혼복에서 여자가 쓸 슬롯 = remaining_female_slots
            # 혼복 1매치당 여자 2슬롯 필요
            if remaining_female_slots < 0 or remaining_female_slots % 2 != 0:
                continue
            
            y = remaining_female_slots // 2  # 혼복 수
            
            # 남자 슬롯 검증
            remaining_male_slots = male_slots - 2 * y
            if remaining_male_slots < 0 or remaining_male_slots % 4 != 0:
                continue
            
            z = remaining_male_slots // 4  # 남복 수
            
            if not can_male_doubles and z > 0:
                continue
            
            # 총 매치 수 검증
            if x + y + z != self.total_matches:
                continue
            
            # 유효한 조합 발견! 점수 계산 (점수가 높을수록 좋음)
            # 소수 성별의 동성복식 + 혼복 균형 맞추기
            
            minority_same_gender = x if num_females < num_males else z
            majority_same_gender = z if num_females < num_males else x
            
            score = 0
            
            # 소수 성별 동성복식: 1개 이상이면 큰 보너스
            if minority_same_gender >= 1:
                score += 200
            if minority_same_gender >= 2:
                score += 100
            
            # 혼복: 적어도 4개 이상은 있어야 재미있음
            if y >= 4:
                score += 150
            elif y >= 2:
                score += 80
            elif y >= 1:
                score += 30
            
            # 다수 성별 동성복식도 적당히
            score += majority_same_gender * 20
            
            # 균형 보너스: 세 가지 타입이 모두 있으면 추가 보너스
            if x > 0 and y > 0 and z > 0:
                score += 100
            
            if score > best_score:
                best_score = score
                best_plan = {'female': x, 'male': z, 'mixed': y}
        
        # 유효한 계획이 없으면 기본값
        if best_plan is None:
            # 혼복만으로 구성
            best_plan = {'female': 0, 'male': 0, 'mixed': self.total_matches}
        
        return best_plan
    
    def _create_match_plan_considering_availability(self):
        """
        각 라운드의 실제 가용 인원을 고려한 매치 계획
        늦참/일퇴가 있는 경우 더 현실적인 계획을 세움
        """
        # 기본 계획 먼저 계산
        base_plan = self._create_match_plan()
        
        # 각 라운드별 가용 인원 확인
        round_constraints = []
        for r in range(1, self.num_rounds + 1):
            males_avail = sum(1 for p in self.males if p.is_available_for_round(r))
            females_avail = sum(1 for p in self.females if p.is_available_for_round(r))
            round_constraints.append({
                'round': r,
                'males': males_avail,
                'females': females_avail,
                'can_female': females_avail >= 4,
                'can_male': males_avail >= 4,
                'can_mixed': males_avail >= 2 and females_avail >= 2,
                'can_double_mixed': males_avail >= 4 and females_avail >= 4,
            })
        
        # 각 타입이 가능한 총 라운드 수 계산
        rounds_for_female = sum(1 for rc in round_constraints if rc['can_female'])
        rounds_for_male = sum(1 for rc in round_constraints if rc['can_male'])
        rounds_for_double_mixed = sum(1 for rc in round_constraints if rc['can_double_mixed'])
        
        # 여복/남복이 가능한 라운드가 제한되면 계획 조정
        max_female_matches = min(base_plan.get('female', 0), rounds_for_female * self.num_courts)
        max_male_matches = min(base_plan.get('male', 0), rounds_for_male * self.num_courts)
        
        # 조정된 계획
        adjusted_female = min(base_plan.get('female', 0), max_female_matches)
        adjusted_male = min(base_plan.get('male', 0), max_male_matches)
        adjusted_mixed = self.total_matches - adjusted_female - adjusted_male
        
        # 혼복이 음수면 조정
        if adjusted_mixed < 0:
            # 여복/남복 중 더 많은 쪽을 줄임
            if adjusted_female > adjusted_male:
                adjusted_female += adjusted_mixed
            else:
                adjusted_male += adjusted_mixed
            adjusted_mixed = 0
        
        return {
            'female': max(0, adjusted_female),
            'male': max(0, adjusted_male),
            'mixed': max(0, adjusted_mixed)
        }
    
    def _get_round_available_counts(self, round_num):
        """특정 라운드에서 가용한 남녀 수 계산"""
        males_available = sum(1 for p in self.males if p.is_available_for_round(round_num))
        females_available = sum(1 for p in self.females if p.is_available_for_round(round_num))
        return males_available, females_available
    
    def _distribute_match_types_to_rounds(self):
        """
        라운드별로 매치 타입을 분배 (인원 제약 + 늦참/일퇴 고려!)
        
        인원 제약:
        - 여복 1매치: 여자 4명 필요
        - 남복 1매치: 남자 4명 필요
        - 혼복 1매치: 여자 2명 + 남자 2명 필요
        
        같은 라운드 조합 제약:
        - 여복 + 여복: 여자 8명 필요
        - 남복 + 남복: 남자 8명 필요
        - 혼복 + 혼복: 여자 4명 + 남자 4명 필요
        - 여복 + 혼복: 여자 6명 필요
        - 남복 + 혼복: 남자 6명 필요
        - 여복 + 남복: 여자 4명 + 남자 4명 (항상 가능)
        
        Returns: {round_num: [match_type, match_type, ...]}
        """
        female_matches = self.match_plan.get('female', 0)
        male_matches = self.match_plan.get('male', 0)
        mixed_matches = self.match_plan.get('mixed', 0)
        
        round_types = {r: [] for r in range(1, self.num_rounds + 1)}
        
        # 라운드별 매치 슬롯 계산
        slots_per_round = self.num_courts
        
        remaining_female = female_matches
        remaining_male = male_matches
        remaining_mixed = mixed_matches
        
        # 라운드별 가용 인원 계산
        round_availability = {}
        for r in range(1, self.num_rounds + 1):
            males_avail, females_avail = self._get_round_available_counts(r)
            round_availability[r] = {'males': males_avail, 'females': females_avail}
        
        round_list = list(range(1, self.num_rounds + 1))
        random.shuffle(round_list)
        
        # 헬퍼 함수: 해당 라운드에서 매치 타입이 가능한지 확인
        def can_add_match_type(r, match_type, current_types):
            avail = round_availability[r]
            males = avail['males']
            females = avail['females']
            
            # 현재 라운드에 이미 배치된 타입에 따른 인원 소모 계산
            used_males = sum(4 if t == 'male' else 2 if t == 'mixed' else 0 for t in current_types)
            used_females = sum(4 if t == 'female' else 2 if t == 'mixed' else 0 for t in current_types)
            
            remaining_males = males - used_males
            remaining_females = females - used_females
            
            if match_type == 'female':
                return remaining_females >= 4
            elif match_type == 'male':
                return remaining_males >= 4
            elif match_type == 'mixed':
                return remaining_males >= 2 and remaining_females >= 2
            return False
        
        # 1단계: 여복/남복 우선 배치 (여복+남복 조합 선호)
        for r in round_list:
            if remaining_female > 0 and remaining_male > 0:
                if can_add_match_type(r, 'female', round_types[r]) and can_add_match_type(r, 'male', round_types[r] + ['female']):
                    round_types[r].append('female')
                    remaining_female -= 1
                    round_types[r].append('male')
                    remaining_male -= 1
        
        # 2단계: 남은 여복 배치 (가용 인원 확인!)
        for r in round_list:
            if len(round_types[r]) >= slots_per_round:
                continue
            
            if remaining_female > 0 and can_add_match_type(r, 'female', round_types[r]):
                current = round_types[r]
                # 이미 여복이 있으면 여복+여복 (8명 필요)
                if 'female' in current:
                    if can_add_match_type(r, 'female', current):
                        round_types[r].append('female')
                        remaining_female -= 1
                # 이미 남복이 있으면 추가 안함 (이미 처리됨)
                elif 'male' in current:
                    pass
                # 빈 라운드
                elif len(current) == 0:
                    round_types[r].append('female')
                    remaining_female -= 1
        
        # 3단계: 남은 남복 배치 (가용 인원 확인!)
        for r in round_list:
            if len(round_types[r]) >= slots_per_round:
                continue
            
            if remaining_male > 0 and can_add_match_type(r, 'male', round_types[r]):
                current = round_types[r]
                # 이미 남복이 있으면 남복+남복 (8명 필요)
                if 'male' in current:
                    if can_add_match_type(r, 'male', current):
                        round_types[r].append('male')
                        remaining_male -= 1
                # 이미 여복이 있으면 남복 추가 가능
                elif 'female' in current:
                    round_types[r].append('male')
                    remaining_male -= 1
                # 빈 라운드
                elif len(current) == 0:
                    round_types[r].append('male')
                    remaining_male -= 1
        
        # 4단계: 혼복 배치 (가용 인원 확인!)
        for r in round_list:
            while len(round_types[r]) < slots_per_round and remaining_mixed > 0:
                if not can_add_match_type(r, 'mixed', round_types[r]):
                    break
                
                round_types[r].append('mixed')
                remaining_mixed -= 1
        
        # 5단계: 소수 성별 참여 보장 - 여복/남복이 불가능한 라운드에 혼복 우선!
        minority_gender = 'F' if len(self.females) < len(self.males) else 'M' if len(self.males) < len(self.females) else None
        
        for r in round_list:
            avail = round_availability[r]
            
            # 소수 성별 복식이 불가능하고 혼복만 가능한 라운드
            if minority_gender == 'F' and avail['females'] < 4 and 'mixed' not in round_types[r]:
                if remaining_mixed > 0 and can_add_match_type(r, 'mixed', round_types[r]):
                    round_types[r].insert(0, 'mixed')  # 맨 앞에 혼복 추가
                    remaining_mixed -= 1
            elif minority_gender == 'M' and avail['males'] < 4 and 'mixed' not in round_types[r]:
                if remaining_mixed > 0 and can_add_match_type(r, 'mixed', round_types[r]):
                    round_types[r].insert(0, 'mixed')
                    remaining_mixed -= 1
        
        # 6단계: 남은 매치 강제 배치 (빈 슬롯에, 가용 인원 확인!)
        for r in round_list:
            while len(round_types[r]) < slots_per_round:
                added = False
                if remaining_mixed > 0 and can_add_match_type(r, 'mixed', round_types[r]):
                    round_types[r].append('mixed')
                    remaining_mixed -= 1
                    added = True
                elif remaining_male > 0 and can_add_match_type(r, 'male', round_types[r]):
                    round_types[r].append('male')
                    remaining_male -= 1
                    added = True
                elif remaining_female > 0 and can_add_match_type(r, 'female', round_types[r]):
                    round_types[r].append('female')
                    remaining_female -= 1
                    added = True
                
                if not added:
                    break
        
        # 7단계: 빈 슬롯 채우기 (계획에 없어도 가능한 매치 추가!)
        # 코트가 놀지 않도록 추가 매치 생성
        for r in round_list:
            while len(round_types[r]) < slots_per_round:
                added = False
                # 우선순위: 남복+혼복 조합이 가장 유연함
                if can_add_match_type(r, 'male', round_types[r]):
                    round_types[r].append('male')
                    added = True
                elif can_add_match_type(r, 'mixed', round_types[r]):
                    round_types[r].append('mixed')
                    added = True
                elif can_add_match_type(r, 'female', round_types[r]):
                    round_types[r].append('female')
                    added = True
                
                if not added:
                    break
        
        # 각 라운드 내 매치 순서 랜덤화
        for r in round_types:
            random.shuffle(round_types[r])
        
        # 라운드 순서도 랜덤하게 섞기
        items = list(round_types.items())
        random.shuffle(items)
        
        new_round_types = {}
        for new_round, (_, types) in enumerate(items, 1):
            new_round_types[new_round] = types
        
        return new_round_types
    
    def get_available_players(self, round_num):
        """해당 라운드에 참가 가능한 선수들"""
        return [p for p in self.participants if p.is_available_for_round(round_num)]
    
    def get_target_games(self):
        """1인당 목표 게임 수 계산"""
        total_slots = self.total_matches * 4
        total_people = len(self.participants)
        if total_people == 0:
            return 4
        
        base = total_slots // total_people
        return base
    
    def get_max_games(self):
        """1인당 최대 게임 수 (목표 + 1)"""
        total_slots = self.total_matches * 4
        total_people = len(self.participants)
        if total_people == 0:
            return 5
        
        base = total_slots // total_people
        extra = total_slots % total_people
        
        # 나머지가 있으면 일부 사람은 +1 가능
        if extra > 0:
            return base + 1
        return base
    
    def get_games_deficit(self, player):
        """목표 대비 부족한 게임 수"""
        target = self.get_target_games()
        played = self.games_played.get(player.id, 0)
        return target - played
    
    def get_match_type_targets(self, player):
        """
        플레이어의 매치 타입별 목표 게임 수 계산
        
        규칙:
        1. 여4남8: 여자 = 여복2 + 혼복2, 남자 = 남복3 + 혼복1
        2. 여6남6: 여자 = 여복3 + 혼복1, 남자 = 남복3 + 혼복1  
        3. 여8남4: 여자 = 여복3 + 혼복1, 남자 = 남복2 + 혼복2
        """
        num_males = len(self.males)
        num_females = len(self.females)
        
        if num_males == 0 or num_females == 0:
            # 단일 성별만 있는 경우
            return {'same': 4, 'mixed': 0}
        
        ratio = num_females / num_males
        
        if player.gender == 'F':  # 여자
            if ratio <= 0.6:  # 여4남8 유형
                return {'female': 2, 'mixed': 2}
            else:  # 여6남6 또는 여8남4
                return {'female': 3, 'mixed': 1}
        else:  # 남자
            if ratio >= 1.6:  # 여8남4 유형
                return {'male': 2, 'mixed': 2}
            else:  # 여4남8 또는 여6남6
                return {'male': 3, 'mixed': 1}
    
    def get_match_type_deficit(self, player, match_type):
        """특정 매치 타입에서 부족한 게임 수"""
        targets = self.get_match_type_targets(player)
        current = self.match_type_count[player.id].get(match_type, 0)
        
        if match_type == 'mixed':
            target = targets.get('mixed', 0)
        elif match_type == 'female':
            target = targets.get('female', 0)
        elif match_type == 'male':
            target = targets.get('male', 0)
        else:
            target = 0
        
        return target - current
    
    def is_at_max_games(self, player):
        """최대 게임 수에 도달했는지"""
        max_games = self.get_max_games()
        played = self.games_played.get(player.id, 0)
        return played >= max_games
    
    def calculate_team_ntrp(self, p1, p2):
        """팀 NTRP 합계"""
        try:
            return float(p1.ntrp) + float(p2.ntrp)
        except:
            return 5.0
    
    def generate_valid_teams(self, match_type, players, strict_max_games=True, round_num=None):
        """주어진 매치 타입에 맞는 유효한 팀 조합 생성"""
        # strict_max_games=True면 최대 게임수 도달 선수 제외
        # strict_max_games=False면 매치 타입 목표를 위해 허용
        # 단, 연속 휴식 중인 선수는 항상 포함!
        
        def should_include(p):
            # 연속 휴식 중이면 반드시 포함
            if round_num:
                rounds_since = round_num - self.last_played_round.get(p.id, 0)
                if rounds_since >= 2:
                    return True
            
            # strict_max_games 체크
            if strict_max_games and self.is_at_max_games(p):
                return False
            
            return True
        
        available = [p for p in players if should_include(p)]
        
        males = [p for p in available if p.gender == 'M']
        females = [p for p in available if p.gender == 'F']
        
        valid_matches = []
        
        if match_type == 'male':
            if len(males) < 4:
                return []
            for four_males in combinations(males, 4):
                m = list(four_males)
                random.shuffle(m)  # 랜덤하게 섞기
                arrangements = [
                    ((m[0], m[1]), (m[2], m[3])),
                    ((m[0], m[2]), (m[1], m[3])),
                    ((m[0], m[3]), (m[1], m[2])),
                ]
                for team_a, team_b in arrangements:
                    valid_matches.append((team_a, team_b, 'male'))
        
        elif match_type == 'female':
            if len(females) < 4:
                return []
            for four_females in combinations(females, 4):
                f = list(four_females)
                random.shuffle(f)  # 랜덤하게 섞기
                arrangements = [
                    ((f[0], f[1]), (f[2], f[3])),
                    ((f[0], f[2]), (f[1], f[3])),
                    ((f[0], f[3]), (f[1], f[2])),
                ]
                for team_a, team_b in arrangements:
                    valid_matches.append((team_a, team_b, 'female'))
        
        elif match_type == 'mixed':
            if len(males) < 2 or len(females) < 2:
                return []
            for two_males in combinations(males, 2):
                for two_females in combinations(females, 2):
                    m = list(two_males)
                    f = list(two_females)
                    random.shuffle(m)
                    random.shuffle(f)
                    arrangements = [
                        ((m[0], f[0]), (m[1], f[1])),
                        ((m[0], f[1]), (m[1], f[0])),
                    ]
                    for team_a, team_b in arrangements:
                        valid_matches.append((team_a, team_b, 'mixed'))
        
        return valid_matches
    
    def evaluate_match(self, team_a, team_b, match_type, round_num, allow_over_max=False):
        """매치 품질 평가 (낮을수록 좋음) - 게임수 균등화 + 매치타입 분배 최우선"""
        score = 0
        all_players = list(team_a) + list(team_b)
        
        # 0. 최대 게임수 초과 방지 (매치 타입 달성을 위해 allow_over_max=True면 완화)
        over_max_count = sum(1 for p in all_players if self.is_at_max_games(p))
        if over_max_count > 0:
            if not allow_over_max:
                return float('inf')  # 절대 선택 안 함
            else:
                # 매치 타입 목표 달성을 위해 허용하되, 큰 페널티 부과
                score += over_max_count * 5000
        
        # 1. 게임 수 균형 (최우선!)
        total_deficit = 0
        for p in all_players:
            deficit = self.get_games_deficit(p)
            total_deficit += deficit
            
            if deficit < 0:  # 이미 목표 초과
                score += abs(deficit) * 10000  # 매우 큰 페널티
            elif deficit == 0:  # 목표 달성
                score += 500  # 페널티 (아직 부족한 사람 우선)
            else:  # 아직 부족
                score -= deficit * 200  # 큰 보너스
        
        # 게임이 가장 부족한 사람들 조합에 보너스
        score -= total_deficit * 100
        
        # 1.5. 매치 타입별 목표 달성 (중요!)
        total_type_deficit = 0
        for p in all_players:
            type_deficit = self.get_match_type_deficit(p, match_type)
            total_type_deficit += type_deficit
            
            if type_deficit < 0:  # 이 타입 목표 초과
                score += abs(type_deficit) * 5000  # 큰 페널티
            elif type_deficit == 0:  # 이 타입 목표 달성
                score += 300  # 페널티
            else:  # 아직 부족
                score -= type_deficit * 300  # 보너스
        
        # 매치 타입 부족한 사람들 조합에 보너스
        score -= total_type_deficit * 150
        
        # 2. 늦참/일퇴 참가자 우선 (긴급도) - 더 강화!
        for p in all_players:
            total_available = sum(1 for r in range(1, self.num_rounds + 1) 
                                  if p.is_available_for_round(r))
            remaining_rounds = sum(1 for r in range(round_num, self.num_rounds + 1) 
                                   if p.is_available_for_round(r))
            deficit = self.get_games_deficit(p)
            
            # 가용 라운드가 전체보다 적은 선수 (늦참/일퇴)
            is_limited = total_available < self.num_rounds
            
            if remaining_rounds > 0 and deficit > 0:
                urgency = deficit / remaining_rounds
                
                # 늦참/일퇴 선수에게 더 큰 보너스
                multiplier = 2.0 if is_limited else 1.0
                
                # 소수 성별이면서 제한된 참가자면 더 큰 보너스
                minority_gender = 'F' if len(self.females) < len(self.males) else 'M' if len(self.males) < len(self.females) else None
                if is_limited and minority_gender and p.gender == minority_gender:
                    multiplier = 3.0
                
                if urgency >= 1:
                    score -= urgency * 2000 * multiplier  # 매우 높은 보너스
                elif urgency >= 0.5:
                    score -= urgency * 1000 * multiplier
                else:
                    score -= urgency * 500 * multiplier
        
        # 3. 연속 휴식 방지 (강제!)
        for p in all_players:
            rounds_since = round_num - self.last_played_round.get(p.id, 0)
            if rounds_since >= 2:  # 2라운드 이상 쉬었으면 반드시 참여
                score -= 100000  # 매우 큰 보너스
            elif rounds_since == 1:  # 1라운드 쉬었으면 우선
                score -= 3000
        
        # 4. NTRP 밸런스
        ntrp_diff = abs(self.calculate_team_ntrp(*team_a) - self.calculate_team_ntrp(*team_b))
        score += ntrp_diff * 5
        
        # 5. 파트너 중복 방지
        if team_a[1].id in self.partner_history.get(team_a[0].id, set()):
            score += 200
        if team_b[1].id in self.partner_history.get(team_b[0].id, set()):
            score += 200
        
        # 6. 상대 중복 방지
        for pa in team_a:
            for pb in team_b:
                if pb.id in self.opponent_history.get(pa.id, set()):
                    score += 30
        
        # 7. 랜덤 요소 (균등화를 깨지 않는 범위에서만!)
        score += random.uniform(-30, 30)
        
        return score
    
    def find_best_match_for_type(self, players, round_num, match_type):
        """특정 매치 타입에 대해 최적의 매치 찾기"""
        # 연속 휴식 중인 선수 파악
        must_play = [
            p for p in players 
            if round_num - self.last_played_round.get(p.id, 0) >= 2
        ]
        
        # 먼저 strict mode로 시도 (연속 휴식 중인 선수는 항상 포함)
        valid_matches = self.generate_valid_teams(match_type, players, strict_max_games=True, round_num=round_num)
        
        # strict mode에서 불가능하면 완화해서 재시도
        if not valid_matches:
            valid_matches = self.generate_valid_teams(match_type, players, strict_max_games=False, round_num=round_num)
        
        if not valid_matches:
            return None, float('inf')
        
        # 연속 휴식 중인 선수가 있으면 해당 선수가 포함된 매치를 우선!
        if must_play:
            must_play_ids = {p.id for p in must_play}
            prioritized = []
            others = []
            
            for match in valid_matches:
                team_a, team_b, mtype = match
                all_in_match = list(team_a) + list(team_b)
                match_player_ids = {p.id for p in all_in_match}
                
                # 연속 휴식 중인 선수가 포함되어 있으면 우선
                if match_player_ids & must_play_ids:
                    prioritized.append(match)
                else:
                    others.append(match)
            
            # 우선 매치가 있으면 그것만 평가
            if prioritized:
                valid_matches = prioritized
        
        # 완전히 랜덤하게 섞기!
        random.shuffle(valid_matches)
        
        best_match = None
        best_score = float('inf')
        
        # 상위 N개만 평가
        for team_a, team_b, mtype in valid_matches[:50]:
            score = self.evaluate_match(team_a, team_b, mtype, round_num, allow_over_max=True)
            
            if score < best_score:
                best_score = score
                best_match = (team_a, team_b, mtype)
        
        return best_match, best_score
    
    def find_any_valid_match(self, players, round_num):
        """가능한 아무 매치나 찾기 (계획된 타입이 불가능할 때)"""
        # 연속 휴식 중인 선수 파악
        must_play = [
            p for p in players 
            if round_num - self.last_played_round.get(p.id, 0) >= 2
        ]
        must_play_males = [p for p in must_play if p.gender == 'M']
        must_play_females = [p for p in must_play if p.gender == 'F']
        
        males = [p for p in players if p.gender == 'M']
        females = [p for p in players if p.gender == 'F']
        
        # 가능한 타입 순서
        possible_types = []
        
        # 연속 휴식 중인 선수가 참여할 수 있는 타입 우선!
        if must_play_females and len(females) >= 4:
            possible_types.append('female')
        if must_play_males and len(males) >= 4:
            possible_types.append('male')
        if (must_play_males or must_play_females) and len(males) >= 2 and len(females) >= 2:
            possible_types.append('mixed')
        
        # 나머지 타입 추가
        if len(males) >= 4 and 'male' not in possible_types:
            possible_types.append('male')
        if len(females) >= 4 and 'female' not in possible_types:
            possible_types.append('female')
        if len(males) >= 2 and len(females) >= 2 and 'mixed' not in possible_types:
            possible_types.append('mixed')
        
        for match_type in possible_types:
            match, score = self.find_best_match_for_type(players, round_num, match_type)
            if match:
                return match, score
        
        return None, float('inf')
    
    def update_history(self, team_a, team_b, match_type, round_num):
        """매치 기록 업데이트"""
        all_players = list(team_a) + list(team_b)
        
        for p in all_players:
            self.games_played[p.id] += 1
            self.match_type_count[p.id][match_type] += 1
            self.last_played_round[p.id] = round_num
        
        # 파트너 기록
        self.partner_history[team_a[0].id].add(team_a[1].id)
        self.partner_history[team_a[1].id].add(team_a[0].id)
        self.partner_history[team_b[0].id].add(team_b[1].id)
        self.partner_history[team_b[1].id].add(team_b[0].id)
        
        # 상대 기록
        for pa in team_a:
            for pb in team_b:
                self.opponent_history[pa.id].add(pb.id)
                self.opponent_history[pb.id].add(pa.id)
    
    def generate_round(self, round_num):
        """한 라운드의 매치들 생성"""
        # 이 라운드에 참가 가능한 전체 선수 (휴식 계산용)
        all_available = self.get_available_players(round_num)
        
        # 연속 휴식 중인 선수 (2라운드 이상 쉬었으면 반드시 참여!)
        must_play_players = [
            p for p in all_available 
            if round_num - self.last_played_round.get(p.id, 0) >= 2
        ]
        
        # 매치 배정용: 최대 게임수에 도달하지 않은 선수 + 연속 휴식 중인 선수
        can_play = [p for p in all_available if not self.is_at_max_games(p)]
        
        # 연속 휴식 중인 선수는 max_games 도달해도 반드시 포함
        for p in must_play_players:
            if p not in can_play:
                can_play.append(p)
        
        # 소수 성별 확인
        minority_gender = 'F' if len(self.females) < len(self.males) else 'M' if len(self.males) < len(self.females) else None
        
        def player_priority(p):
            deficit = self.get_games_deficit(p)
            total_available = sum(1 for r in range(1, self.num_rounds + 1) if p.is_available_for_round(r))
            remaining_rounds = sum(1 for r in range(round_num, self.num_rounds + 1) if p.is_available_for_round(r))
            
            # 연속 휴식 체크 (최우선!)
            rounds_since_played = round_num - self.last_played_round.get(p.id, 0)
            must_play = rounds_since_played >= 2  # 2라운드 이상 쉬었으면 반드시 참여
            
            # 긴급도: 부족한 게임수 / 남은 라운드
            urgency = deficit / remaining_rounds if remaining_rounds > 0 else 0
            
            # 소수 성별이면서 제한된 참가자면 최우선
            is_limited = total_available < self.num_rounds
            is_minority = minority_gender and p.gender == minority_gender
            
            priority = 0
            if must_play:
                priority = 10000  # 연속 휴식 방지 최우선!
            elif is_limited and is_minority:
                priority = 1000
            elif is_limited:
                priority = 500
            elif is_minority:
                priority = 100
            
            return (-priority, -deficit, -urgency, random.random())
        
        # 우선순위로 정렬
        can_play = sorted(can_play, key=player_priority)
        
        matches = []
        players_in_match = []  # 이 라운드에서 매치에 배정된 선수들
        remaining_can_play = can_play.copy()
        
        # 이 라운드에 예정된 매치 타입들
        planned_types = self.round_match_types.get(round_num, [])
        
        for court_idx, planned_type in enumerate(planned_types):
            if len(remaining_can_play) < 4:
                break
            
            # 계획된 타입으로 먼저 시도
            match, score = self.find_best_match_for_type(remaining_can_play, round_num, planned_type)
            
            # 안 되면 다른 타입 시도
            if not match:
                match, score = self.find_any_valid_match(remaining_can_play, round_num)
            
            if match:
                team_a, team_b, match_type = match
                
                self.update_history(team_a, team_b, match_type, round_num)
                
                for p in list(team_a) + list(team_b):
                    players_in_match.append(p)
                    if p in remaining_can_play:
                        remaining_can_play.remove(p)
                
                matches.append({
                    'round': round_num,
                    'court': court_idx + 1,
                    'team_a': team_a,
                    'team_b': team_b,
                    'match_type': match_type,
                })
        
        # 코트 번호 재배치: 남복 > 혼복 > 여복
        matches = self._reorder_courts(matches)
        
        # 휴식 = 참가 가능한 전체 선수 - 매치에 배정된 선수
        resting = [p for p in all_available if p not in players_in_match]
        
        return matches, resting
    
    def _reorder_courts(self, matches):
        """코트 번호 재배치 - 남복 > 혼복 > 여복 순서로 코트 1에 배치"""
        if len(matches) <= 1:
            return matches
        
        type_priority = {'male': 0, 'mixed': 1, 'female': 2}
        sorted_matches = sorted(matches, key=lambda m: type_priority.get(m.get('match_type', 'mixed'), 2))
        
        for i, match in enumerate(sorted_matches):
            match['court'] = i + 1
        
        return sorted_matches
    
    def generate_matches(self):
        """전체 대진표 생성"""
        schedule = []
        
        for round_num in range(1, self.num_rounds + 1):
            matches, resting = self.generate_round(round_num)
            schedule.append({
                'round': round_num,
                'matches': matches,
                'resting': resting,
            })
        
        return schedule


def generate_match_schedule(participants, num_courts=2, num_rounds=6):
    """대진표 생성 헬퍼 함수"""
    maker = MatchMaker(participants, num_courts, num_rounds)
    return maker.generate_matches()
