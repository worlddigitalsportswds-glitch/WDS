from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_web, daemon=True).start()

import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from typing import Optional
import re

# ========================================================
# [설정 정보]
BROADCAST_CHANNEL_ID = 1555555333894832158  # WDS 중계 배정 및 전광판 채널 ID
GUILD_ID = 1554481615864991764
# ========================================================

latest_broadcast_data = "아직 중계 배정 채널에 등록된 중계 정보가 없습니다."
live_scoreboard_message_id = None

# ⚽ 경기별(운영본부 지정 ID 기준) 동적 추가시간 저장소
MATCH_OVERTIME_CONFIG = {}

REALTIME_RANK_DATA = {
    "kbo": "데이터 로딩 중...",
    "kleague": "데이터 로딩 중..."
}

# 🎯 2026 시즌 대진 DB (사전 지정된 ID 없음, 초기 상태는 None)
REAL_SEASON_SCHEDULE_DB = {
    "20261010": {
        "kbo": [
            {"id": None, "away": "LG 트윈스", "home": "롯데 자이언츠", "time": "14:00", "stadium": "부산 사직야구장"},
            {"id": None, "away": "NC 다이노스", "home": "한화 이글스", "time": "17:00", "stadium": "대전 한화생명볼파크"},
            {"id": None, "away": "SSG 랜더스", "home": "KIA 타이거즈", "time": "17:00", "stadium": "광주 기아 챔피언스 필드"}
        ],
        "kleague": [
            {"id": None, "away": "제주 SK FC", "home": "FC 서울", "time": "14:00", "stadium": "서울월드컵경기장"},
            {"id": None, "away": "FC 안양", "home": "김천상무", "time": "16:30", "stadium": "김천종합운동장"}
        ]
    },
    "20261011": {
        "kbo": [
            {"id": None, "away": "kt wiz", "home": "삼성 라이온즈", "time": "14:00", "stadium": "대구 삼성 라이온즈 파크"},
            {"id": None, "away": "롯데 자이언츠", "home": "KIA 타이거즈", "time": "14:00", "stadium": "광주 기아 챔피언스 필드"}
        ],
        "kleague": [
            {"id": None, "away": "울산 HD FC", "home": "광주 FC", "time": "14:00", "stadium": "광주축구전용구장"}
        ]
    },
    "20261012": {
        "kbo": [
            {"id": None, "away": "LG 트윈스", "home": "KIA 타이거즈", "time": "18:30", "stadium": "광주 기아 챔피언스 필드"},
            {"id": None, "away": "롯데 자이언츠", "home": "두산 베어스", "time": "18:30", "stadium": "서울 잠실야구장"},
            {"id": None, "away": "kt wiz", "home": "삼성 라이온즈", "time": "18:30", "stadium": "대구 삼성 라이온즈 파크"}
        ],
        "kleague": []
    },
    "20261014": {
        "kbo": [{"id": None, "away": "두산 베어스 (5위)", "home": "정규시즌 4위팀 [WC 1차전]", "time": "18:30", "stadium": "정규 4위팀 홈구장"}],
        "kleague": []
    },
    "20261015": {
        "kbo": [{"id": None, "away": "두산 베어스 (5위)", "home": "정규시즌 4위팀 [WC 2차전 필요시]", "time": "18:30", "stadium": "정규 4위팀 홈구장"}],
        "kleague": []
    },
    "20261017": {
        "kbo": [{"id": None, "away": "와일드카드 승리팀", "home": "정규시즌 3위팀 [준PO 1차전]", "time": "14:00", "stadium": "정규 3위팀 홈구장"}],
        "kleague": [{"id": None, "away": "부천 FC 1995", "home": "울산 HD FC (32R)", "time": "16:30", "stadium": "울산 문수축구경기장"}]
    },
    "20261018": {
        "kbo": [{"id": None, "away": "와일드카드 승리팀", "home": "정규시즌 3위팀 [준PO 2차전]", "time": "14:00", "stadium": "정규 3위팀 홈구장"}],
        "kleague": [
            {"id": None, "away": "제주 SK FC", "home": "전북 현대 (32R)", "time": "14:00", "stadium": "전주월드컵경기장"},
            {"id": None, "away": "광주 FC", "home": "대전 하나 시티즌 (32R)", "time": "14:00", "stadium": "대전월드컵경기장"},
            {"id": None, "away": "FC 안양", "home": "포항 스틸러스 (32R)", "time": "16:30", "stadium": "포항스틸야드"},
            {"id": None, "away": "인천 유나이티드", "home": "강원 FC (32R)", "time": "16:30", "stadium": "춘천송암스포츠타운"},
            {"id": None, "away": "김천상무", "home": "FC 서울 (32R)", "time": "16:30", "stadium": "서울월드컵경기장"}
        ]
    },
    "20261024": {
        "kbo": [],
        "kleague": [
            {"id": None, "away": "강원 FC", "home": "FC 서울 (정규 최종 33R)", "time": "14:00", "stadium": "서울월드컵경기장"},
            {"id": None, "away": "전북 현대", "home": "FC 안양 (정규 최종 33R)", "time": "14:00", "stadium": "안양종합운동장"},
            {"id": None, "away": "광주 FC", "home": "부천 FC 1995 (정규 최종 33R)", "time": "14:00", "stadium": "부천종합운동장"},
            {"id": None, "away": "포항 스틸러스", "home": "울산 HD FC (정규 최종 33R)", "time": "14:00", "stadium": "울산 문수축구경기장"},
            {"id": None, "away": "제주 SK FC", "home": "인천 유나이티드 (정규 최종 33R)", "time": "14:00", "stadium": "인천축구전용경기장"},
            {"id": None, "away": "대전 하나 시티즌", "home": "김천상무 (정규 최종 33R)", "time": "14:00", "stadium": "김천종합운동장"}
        ]
    }
}

class SportsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("🤖 글로벌 명령어 트리 준비 완료")

bot = SportsBot()

async def fetch_latest_rankings():
    global REALTIME_RANK_DATA
    REALTIME_RANK_DATA["kbo"] = (
        "1. kt wiz (88승 5무 49패)\n"
        "2. 삼성 라이온즈 (83승 3무 56패)\n"
        "3. KIA 타이거즈 (77승 2무 62패)\n"
        "4. LG 트윈스 (77승 1무 64패)\n"
        "5. 두산 베어스 (73승 5무 65패)\n"
        "6. SSG 랜더스 (65승 5무 73패)\n"
        "7. 롯데 자이언츠 (62승 3무 76패)\n"
        "8. NC 다이노스 (63승 2무 78패)\n"
        "9. 한화 이글스 (57승 4무 82패)\n"
        "10. 키움 히어로즈 (50승 4무 90패)"
    )

    REALTIME_RANK_DATA["kleague"] = (
        "1. FC 서울 [31경기 65점]\n"
        "2. 울산 HD FC [30경기 47점]\n"
        "3. 강원 FC [31경기 46점]\n"
        "4. 제주 SK FC [31경기 46점]\n"
        "5. 전북 현대 모터스 [31경기 44점]\n"
        "6. 대전 하나 시티즌 [31경기 43점]\n"
        "7. 인천 유나이티드 [31경기 42점]\n"
        "8. FC 안양 [31경기 41점]\n"
        "9. 포항 스틸러스 [31경기 40점]\n"
        "10. 김천상무 [31경기 33점]\n"
        "11. 부천 FC 1995 [31경기 32점]\n"
        "12. 광주 FC [30경기 15점]"
    )

@bot.event
async def on_ready():
    global latest_broadcast_data
    print(f'🤖 로그인 성공: {bot.user.name} (ID: {bot.user.id})')
    print('----------------------------------------')
    
    try:
        channel = bot.get_channel(BROADCAST_CHANNEL_ID)
        if channel:
            async for message in channel.history(limit=1):
                latest_broadcast_data = message.content
                print(f"[초기화 성공] 최신 WDS 중계 배정 메시지 로드 완료")
    except Exception as e:
        print(f"[오류] 메시지 불러오기 실패: {e}")

    await fetch_latest_rankings()
    
    if not auto_update_scoreboard.is_running():
        auto_update_scoreboard.start()

@bot.event
async def on_message(message: discord.Message):
    global latest_broadcast_data
    if message.author == bot.user:
        return
    if message.channel.id == BROADCAST_CHANNEL_ID:
        latest_broadcast_data = message.content
        print(f"[알림] WDS 중계 배정 메시지 갱신됨")
    await bot.process_commands(message)


# ⚡ 수동 명령어 동기화 (!sync 명령어)
@bot.command(name="sync")
async def sync_commands(ctx):
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ 명령어 동기화 성공! 총 {len(synced)}개의 명령어가 적용되었습니다.")
    except Exception as e:
        await ctx.send(f"❌ 동기화 에러: {e}")


# 🆔 !ID 명령어: 중복 방지 및 입력 필수 지정 명령어
@bot.command(name="ID")
@commands.has_role("WDS 운영본부")
async def set_match_id(ctx, match_keyword: str, new_id: int):
    now_kst = datetime.utcnow() + timedelta(hours=9)
    today_str = now_kst.strftime("%Y%m%d")

    if today_str not in REAL_SEASON_SCHEDULE_DB:
        await ctx.send("❌ 오늘 날짜에 등록된 경기 일정이 없습니다.")
        return

    # 1️⃣ [중복 방지 검증] 이미 다른 경기에 사용 중인 ID인지 전체 DB 탐색
    duplicate_match_name = None
    for date_key, categories in REAL_SEASON_SCHEDULE_DB.items():
        for cat_name, matches in categories.items():
            for m in matches:
                if m.get("id") == new_id:
                    # 현재 설정하려는 대상 경기가 아닌 경우에만 중복으로 처리
                    if not (match_keyword in m["away"] or match_keyword in m["home"]):
                        duplicate_match_name = f"{m['away']} vs {m['home']}"
                        break
            if duplicate_match_name:
                break
        if duplicate_match_name:
            break

    if duplicate_match_name:
        await ctx.send(f"⚠️ 이미 **`{duplicate_match_name}`** 경기에 적용된 경기 ID입니다. 다른 ID를 입력해주세요.")
        return

    # 2️⃣ 키워드로 오늘 경기 찾아서 ID 부여
    found = False
    for category in ["kbo", "kleague"]:
        for match in REAL_SEASON_SCHEDULE_DB[today_str][category]:
            if match_keyword in match["away"] or match_keyword in match["home"]:
                old_id = match.get("id")
                match["id"] = new_id
                found = True
                old_id_str = f"[ID:{old_id}]" if old_id is not None else "[미지정]"
                await ctx.send(f"🎯 **[경기 ID 부여 완료]** `{match['away']} vs {match['home']}` 경기의 ID가 **{old_id_str}** ➔ **[ID:{new_id}]** (으)로 등록되었습니다!")
                break
        if found:
            break

    if not found:
        await ctx.send(f"❌ 오늘 경기 대진 중 `{match_keyword}` 팀이 포함된 경기를 찾을 수 없습니다.")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("⛔ 이 명령어를 사용할 수 있는 권한이 없습니다. (**WDS 운영본부** 역할이 필요합니다)")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ 인자가 부족합니다. 사용법을 확인해주세요!\n• ID 부여: `!ID 롯데 101` 또는 `!ID 서울 201`\n• 추가시간 정정: `!추가시간 101 2/30`")
    else:
        print(f"[명령어 오류 발생]: {error}")


def get_match_overtime(match_id):
    if match_id not in MATCH_OVERTIME_CONFIG:
        MATCH_OVERTIME_CONFIG[match_id] = {"first_half_extra": 0.0, "second_half_extra": 0.0}
    return MATCH_OVERTIME_CONFIG[match_id]


def calculate_match_status_by_id(category, start_time_str, date_str, match_id):
    now_kst = datetime.utcnow() + timedelta(hours=9)
    overtime_data = get_match_overtime(match_id)
    
    try:
        match_dt = datetime.strptime(f"{date_str} {start_time_str}", "%Y%m%d %H:%M")
    except ValueError:
        return f"📅 **[경기 예정]** ({start_time_str})"

    diff_seconds = (now_kst - match_dt).total_seconds()
    diff_minutes = int(diff_seconds // 60)
    exact_minutes_float = diff_seconds / 60.0

    if diff_minutes < 0:
        abs_mins = abs(diff_minutes)
        return f"⏳ **[경기 예정]** (시작까지 {abs_mins}분 남음 / {start_time_str})"

    fh_extra = overtime_data["first_half_extra"]
    sh_extra = overtime_data["second_half_extra"]
    
    max_duration_float = 210.0 if category == 'kbo' else (105.0 + fh_extra + sh_extra)

    if exact_minutes_float >= max_duration_float:
        after_finish_seconds = diff_seconds - (max_duration_float * 60)
        after_mins = int(after_finish_seconds // 60)
        hours = after_mins // 60
        mins = after_mins % 60
        time_after_str = f"{hours}시간 {mins}분" if hours > 0 else f"{mins}분"
        return f"🏁 **[경기 종료]** (종료 후 {time_after_str} 경과 / {start_time_str} 시작)"

    id_label = f"ID:{match_id}" if match_id is not None else "ID:미지정"

    if category == 'kbo':
        inning_cycle = exact_minutes_float / 20.0
        inning = int(inning_cycle) + 1
        remainder = (inning_cycle - int(inning_cycle)) * 20.0
        half = "초" if remainder < 10.0 else "말"
        
        inning_str = "연장전 진행 중" if inning > 9 else f"{inning}회 {half}"
        return f"🎙️ **[경기 진행 중]** [{id_label}] ({inning_str} | 시작 후 {diff_minutes}분 경과)"
    
    else:
        fh_end = 45.0
        fh_extra_end = 45.0 + fh_extra
        ht_end = fh_extra_end + 15.0
        sh_end = ht_end + 45.0
        sh_extra_end = sh_end + sh_extra
        
        if exact_minutes_float < fh_end:
            detail = f"전반전 {diff_minutes if diff_minutes > 0 else 1}분 진행 중"
        elif fh_end <= exact_minutes_float < fh_extra_end:
            it_sec = diff_seconds - (fh_end * 60)
            it_min = int(it_sec // 60) + 1
            detail = f"전반전 45+{it_min}분 (추가시간)"
        elif fh_extra_end <= exact_minutes_float < ht_end:
            rem_sec = (ht_end * 60) - diff_seconds
            rem_ht = max(1, int(rem_sec // 60) + 1)
            detail = f"하프타임 휴식 중 (남은 휴식 약 {rem_ht}분)"
        elif ht_end <= exact_minutes_float < sh_end:
            sf_sec = diff_seconds - (ht_end * 60)
            sf_min = int(sf_sec // 60) + 1
            detail = f"후반전 {sf_min}분 진행 중"
        elif sh_end <= exact_minutes_float < sh_extra_end:
            it2_sec = diff_seconds - (sh_end * 60)
            it2_min = int(it2_sec // 60) + 1
            detail = f"후반전 90+{it2_min}분 (추가시간)"
        else:
            detail = "경기 종료 직전"

        return f"🎙️ **[경기 진행 중]** [{id_label}] ({detail} | 시작 후 {diff_minutes}분 경과)"


# ⚽ 추가시간 설정
@bot.command(name="추가시간")
@commands.has_role("WDS 운영본부")
async def set_extra_time(ctx, match_id: int, time_input: str):
    try:
        is_negative = time_input.startswith('-')
        clean_input = time_input.lstrip('-')
        
        if '/' in clean_input:
            parts = clean_input.split('/')
            mins_part = float(parts[0])
            secs_part = float(parts[1])
            delta_val = mins_part + (secs_part / 60.0)
        else:
            delta_val = float(clean_input)
            
        if is_negative:
            delta_val = -delta_val

    except ValueError:
        await ctx.send("❌ 올바른 형식으로 입력해주세요! (예: `!추가시간 101 2/30` 또는 `!추가시간 201 -0/30`)")
        return

    overtime_data = get_match_overtime(match_id)
    now_kst = datetime.utcnow() + timedelta(hours=9)
    time_match = re.search(r'(\d{1,2}):(\d{2})', latest_broadcast_data) or re.search(r'(\d{1,2})\s*시\s*(\d{1,2})?\s*분?', latest_broadcast_data)
    
    total_delta_sec = delta_val * 60
    abs_sec = abs(int(round(total_delta_sec)))
    m_str = abs_sec // 60
    s_str = abs_sec % 60
    sign_char = "-" if delta_val < 0 else "+"
    input_desc = f"{sign_char}{m_str}분 {s_str}초" if m_str > 0 else f"{sign_char}{s_str}초"

    if time_match:
        if ':' in time_match.group(0):
            hour, minute = int(time_match.group(1)), int(time_match.group(2))
        else:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            
        match_start = now_kst.replace(hour=hour, minute=minute, second=0, microsecond=0)
        diff_mins = int((now_kst - match_start).total_seconds() // 60)
        
        if 45 <= diff_mins <= 104:
            overtime_data["first_half_extra"] += delta_val
            tot = overtime_data["first_half_extra"]
            tot_m, tot_s = int(tot), int(round((tot - int(tot)) * 60))
            await ctx.send(f"⏱️ **[[ID:{match_id}] 전반 추가시간 정정/누적]** ({input_desc}) ➔ 현재 전반 총 추가시간: **+{tot_m}분 {tot_s}초**")
        elif diff_mins >= 105:
            overtime_data["second_half_extra"] += delta_val
            tot = overtime_data["second_half_extra"]
            tot_m, tot_s = int(tot), int(round((tot - int(tot)) * 60))
            await ctx.send(f"⏱️ **[[ID:{match_id}] 후반 추가시간 정정/누적]** ({input_desc}) ➔ 현재 후반 총 추가시간: **+{tot_m}분 {tot_s}초**")
        else:
            overtime_data["second_half_extra"] += delta_val
            tot = overtime_data["second_half_extra"]
            tot_m, tot_s = int(tot), int(round((tot - int(tot)) * 60))
            await ctx.send(f"⏱️ **[[ID:{match_id}] 추가시간 정정/누적]** ({input_desc}) ➔ 현재 총 추가시간: **+{tot_m}분 {tot_s}초** (현재 경과: {diff_mins}분)")
    else:
        overtime_data["second_half_extra"] += delta_val
        tot = overtime_data["second_half_extra"]
        tot_m, tot_s = int(tot), int(round((tot - int(tot)) * 60))
        await ctx.send(f"⏱️ **[[ID:{match_id}] 추가시간 정정/누적]** ({input_desc}) ➔ 현재 총 추가시간: **+{tot_m}분 {tot_s}초**")


def get_official_sports_schedule(category, date_str):
    formatted_date = f"{date_str[:4]}년 {date_str[4:6]}월 {date_str[6:]}일"
    category_name = "KBO 리그" if category == 'kbo' else "K리그 1"
    
    if date_str in REAL_SEASON_SCHEDULE_DB and REAL_SEASON_SCHEDULE_DB[date_str][category]:
        matches = REAL_SEASON_SCHEDULE_DB[date_str][category]
        match_list = []
        for m in matches:
            match_id = m.get('id')
            id_display = f"ID:{match_id}" if match_id is not None else "ID:미지정"
            status_text = calculate_match_status_by_id(category, m['time'], date_str, match_id)
            stadium_info = f" | 📍 {m.get('stadium', '홈구장')}"
            match_list.append(f"• **[{id_display}]** {m['away']} vs {m['home']} ({m['time']}{stadium_info}) ➔ {status_text}")
        return "\n".join(match_list)
    else:
        dt = datetime.strptime(date_str, "%Y%m%d")
        if category == 'kbo' and dt.weekday() == 0:
            return f"• [{formatted_date}] KBO 월요일 정기 휴식일입니다."
        return f"• [{formatted_date}] 예정된 {category_name} 경기가 없거나 휴식일입니다."


def get_single_weekly_schedule_summary(category):
    now_kst = datetime.utcnow() + timedelta(hours=9)
    weekly_text = []

    for i in range(7):
        target_dt = now_kst + timedelta(days=i)
        target_date_str = target_dt.strftime("%Y%m%d")
        day_str = target_dt.strftime("%m/%d(%a)")
        
        day_matches = []
        if target_date_str in REAL_SEASON_SCHEDULE_DB:
            for m in REAL_SEASON_SCHEDULE_DB[target_date_str].get(category, []):
                match_id = m.get('id')
                id_display = f"ID:{match_id}" if match_id is not None else "ID:미지정"
                stadium = m.get('stadium', '홈구장')
                day_matches.append(f"• [{id_display}] {m['away']} vs {m['home']} ({m['time']} | 📍 {stadium})")

        if not day_matches:
            day_matches.append("• 예정된 경기 없음 (휴식일)")

        weekly_text.append(f"📌 **{day_str}**\n" + "\n".join(day_matches))

    return "\n\n".join(weekly_text)


def parse_and_analyze_broadcast(text):
    if not text or text == "아직 중계 배정 채널에 등록된 중계 정보가 없습니다.":
        return "등록된 중계 배정 정보가 없습니다.", "배정된 중계 경기가 없습니다."

    now_kst = datetime.utcnow() + timedelta(hours=9)
    kor_time_match = re.search(r'(\d{1,2})\s*시\s*(\d{1,2})?\s*분?', text)
    colon_time_match = re.search(r'(\d{1,2}):(\d{2})', text)

    hour, minute = 0, 0
    time_found = False

    if kor_time_match:
        hour = int(kor_time_match.group(1))
        minute = int(kor_time_match.group(2)) if kor_time_match.group(2) else 0
        time_found = True
    elif colon_time_match:
        hour = int(colon_time_match.group(1))
        minute = int(colon_time_match.group(2))
        time_found = True

    is_baseball = any(keyword in text for keyword in ['야구', 'KBO', '포스트시즌', '회', '말', '초', '타자', 'LG', 'KT', '삼성', 'KIA', '한화', '두산', 'SSG', '롯데', 'NC', '키움'])
    overtime_data = get_match_overtime(1)

    if time_found:
        match_start = now_kst.replace(hour=hour, minute=minute, second=0, microsecond=0)
        diff_seconds = (now_kst - match_start).total_seconds()
        diff_minutes = int(diff_seconds // 60)
        exact_mins_float = diff_seconds / 60.0

        if diff_minutes < 0:
            status_text = f"⏳ **[중계 예정]** (시작까지 {abs(diff_minutes)}분 남음 / {hour:02d}:{minute:02d} 시작)"
        else:
            fh_extra = overtime_data["first_half_extra"]
            sh_extra = overtime_data["second_half_extra"]
            max_dur_float = 210.0 if is_baseball else (105.0 + fh_extra + sh_extra)
            
            if exact_mins_float >= max_dur_float:
                after_sec = diff_seconds - (max_dur_float * 60)
                after_mins = int(after_sec // 60)
                hours = after_mins // 60
                mins = after_mins % 60
                after_str = f"{hours}시간 {mins}분" if hours > 0 else f"{mins}분"
                status_text = f"🏁 **[중계 종료]** (종료 후 {after_str} 경과 / {hour:02d}:{minute:02d} 시작)"
            else:
                if is_baseball:
                    inning_cycle = exact_mins_float / 20.0
                    total_innings = int(inning_cycle) + 1
                    remainder = (inning_cycle - int(inning_cycle)) * 20.0
                    half = "초" if remainder < 10.0 else "말"
                    
                    inning_info = "연장전 진행 중" if total_innings > 9 else f"{total_innings}회 {half}"
                    status_text = f"🎙️ **[실시간 중계 중]** [ID:미지정] ({inning_info} | 시작 후 {diff_minutes}분 경과)"
                else:
                    fh_end = 45.0
                    fh_extra_end = 45.0 + fh_extra
                    ht_end = fh_extra_end + 15.0
                    sh_end = ht_end + 45.0
                    sh_extra_end = sh_end + sh_extra
                    
                    if exact_mins_float < fh_end:
                        status_info = f"전반전 {diff_minutes if diff_minutes > 0 else 1}분 진행 중"
                    elif fh_end <= exact_minutes_float < fh_extra_end:
                        it_sec = diff_seconds - (fh_end * 60)
                        it_min = int(it_sec // 60) + 1
                        status_info = f"전반전 45+{it_min}분 (추가시간)"
                    elif fh_extra_end <= exact_minutes_float < ht_end:
                        rem_sec = (ht_end * 60) - diff_seconds
                        rem_ht = max(1, int(rem_sec // 60) + 1)
                        status_info = f"하프타임 휴식 중 (남은 휴식 약 {rem_ht}분)"
                    elif ht_end <= exact_minutes_float < sh_end:
                        sf_sec = diff_seconds - (ht_end * 60)
                        sf_min = int(sf_sec // 60) + 1
                        status_info = f"후반전 {sf_min}분 진행 중"
                    elif sh_end <= exact_minutes_float < sh_extra_end:
                        it2_sec = diff_seconds - (sh_end * 60)
                        it2_min = int(it2_sec // 60) + 1
                        status_info = f"후반전 90+{it2_min}분 (추가시간)"
                    else:
                        status_info = "경기 종료 직전"
                    status_text = f"🎙️ **[실시간 중계 중]** [ID:미지정] ({status_info} | 시작 후 {diff_minutes}분 경과)"
    else:
        status_text = "🎙️ **[중계 배정됨]** (시작 시각 패턴 감지 실패)"

    return text, status_text


@tasks.loop(seconds=10)
async def auto_update_scoreboard():
    global live_scoreboard_message_id
    channel = bot.get_channel(BROADCAST_CHANNEL_ID)
    if not channel:
        return

    await fetch_latest_rankings()

    now_kst = datetime.utcnow() + timedelta(hours=9)
    today_str = now_kst.strftime("%Y%m%d")
    formatted_date = f"{today_str[:4]}년 {today_str[4:6]}월 {today_str[6:]}일"

    kbo_info = get_official_sports_schedule('kbo', today_str)
    kleague_info = get_official_sports_schedule('kleague', today_str)

    embed = discord.Embed(
        title=f"🏟️ WDS 실시간 경기 전광판 ({formatted_date})",
        description=f"⏰ **마지막 자동 갱신 시각:** `{now_kst.strftime('%H:%M:%S')}` (10초 주기)",
        color=0x00ff7f
    )
    embed.add_field(name="⚾ KBO 리그 현황", value=kbo_info, inline=False)
    embed.add_field(name="⚽ K리그 1 현황", value=kleague_info, inline=False)
    embed.set_footer(text="WDS 운영본부 실시간 중계 시스템 | 10초마다 자동 갱신됨")

    try:
        if live_scoreboard_message_id:
            msg = await channel.fetch_message(live_scoreboard_message_id)
            await msg.edit(embed=embed)
        else:
            async for msg in channel.history(limit=10):
                if msg.author == bot.user and "WDS 실시간 경기 전광판" in (msg.embeds[0].title if msg.embeds else ""):
                    live_scoreboard_message_id = msg.id
                    await msg.edit(embed=embed)
                    return
            
            new_msg = await channel.send(embed=embed)
            live_scoreboard_message_id = new_msg.id
    except Exception as e:
        print(f"[전광판 자동 갱신 에러]: {e}")
        live_scoreboard_message_id = None


# 1️⃣ /오늘의경기
@bot.tree.command(name="오늘의경기", description="오늘 진행되는 KBO 및 K리그1 전체 경기 일정을 안내합니다.")
async def todays_match(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    
    now_kst = datetime.utcnow() + timedelta(hours=9)
    today_str = now_kst.strftime("%Y%m%d")
    formatted_date = f"{today_str[:4]}년 {today_str[4:6]}월 {today_str[6:]}일"
    
    kbo_info = get_official_sports_schedule('kbo', today_str)
    kleague_info = get_official_sports_schedule('kleague', today_str)

    embed = discord.Embed(title=f"🏟️ 오늘의 전체 실시간 경기 현황 ({formatted_date})", color=0x2b90d9)
    embed.add_field(name="⚾ KBO 리그 대진", value=kbo_info, inline=False)
    embed.add_field(name="⚽ K리그 1 대진", value=kleague_info, inline=False)
    embed.set_footer(text="WDS 스포츠 안내 봇 | ⚠️ ID 미지정 경기는 !ID 명령어로 등록하세요")
    await interaction.followup.send(embed=embed)


# 2️⃣ /중계일정
@bot.tree.command(name="중계일정", description="WDS 중계 배정 채널의 메시지를 실시간 분석하여 안내합니다.")
async def broadcast_schedule(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    
    now_kst = datetime.utcnow() + timedelta(hours=9)
    today_str = now_kst.strftime("%Y%m%d")
    formatted_date = f"{today_str[:4]}년 {today_str[4:6]}월 {today_str[6:]}일"
    
    broadcast_msg, status_analysis = parse_and_analyze_broadcast(latest_broadcast_data)
    
    embed = discord.Embed(title=f"🎙️ WDS 실시간 중계 현황 ({formatted_date})", color=0x7289da)
    embed.add_field(name="📢 WDS 중계 배정 내용 (채널 연동)", value=broadcast_msg if broadcast_msg.strip() else "등록된 배정 정보가 없습니다.", inline=False)
    embed.add_field(name="⏱️ 시작 시각 기반 실시간 진행 분석", value=status_analysis, inline=False)
    embed.set_footer(text="WDS 가상 스포츠 방송국 | 실시간 자동 계산")
    await interaction.followup.send(embed=embed)


# 3️⃣ /경기일정
@bot.tree.command(name="경기일정", description="원하는 리그를 선택하여 향후 주간 일정 또는 특정 날짜의 경기를 조회합니다.")
@app_commands.choices(리그=[
    app_commands.Choice(name="⚾ KBO 리그", value="kbo"),
    app_commands.Choice(name="⚽ K리그 1", value="kleague")
])
async def match_schedule(interaction: discord.Interaction, 리그: app_commands.Choice[str], 날짜: Optional[str] = None):
    await interaction.response.defer(thinking=True)
    
    league_val = 리그.value
    league_title = "KBO 리그" if league_val == "kbo" else "K리그 1"
    color_code = 0x2b90d9 if league_val == "kbo" else 0x00aa55

    if not 날짜:
        weekly_summary = get_single_weekly_schedule_summary(league_val)
        embed = discord.Embed(
            title=f"📅 WDS 스포츠 - {league_title} 향후 7일간 일정",
            description=weekly_summary,
            color=color_code
        )
        embed.set_footer(text="특정 날짜의 세부 상태를 보려면 날짜를 함께 입력하세요. (예: 20261010)")
        await interaction.followup.send(embed=embed)
        return

    clean_date = 날짜.replace("-", "").replace(" ", "").replace(".", "")
    if len(clean_date) != 8 or not clean_date.isdigit():
        await interaction.followup.send("날짜 형식은 8자리 숫자로 입력해주세요! (예: `20261024`)")
        return

    target_date = clean_date
    formatted_date = f"{target_date[:4]}년 {target_date[4:6]}월 {target_date[6:]}일"
    
    schedule_info = get_official_sports_schedule(league_val, target_date)
    
    embed = discord.Embed(title=f"📅 {league_title} 상세 경기 일정 ({formatted_date})", color=color_code)
    embed.add_field(name="🏆 경기 대진 및 실시간 현황", value=schedule_info, inline=False)
    embed.set_footer(text="WDS 스포츠 안내 봇 | ⚠️ ID 미지정 경기는 !ID 명령어로 등록하세요")
    
    await interaction.followup.send(embed=embed)


# 4️⃣ /순위
@bot.tree.command(name="순위", description="KBO 리그 또는 K리그 1의 실시간 팀 순위를 안내합니다.")
@app_commands.choices(리그=[
    app_commands.Choice(name="⚾ KBO 리그", value="kbo"),
    app_commands.Choice(name="⚽ K리그 1", value="kleague")
])
async def team_rank(interaction: discord.Interaction, 리그: app_commands.Choice[str]):
    await interaction.response.defer(thinking=True)
    
    await fetch_latest_rankings()
    
    if 리그.value == "kbo":
        title = "⚾ KBO 리그 실시간 순위 현황"
        rank_list = REALTIME_RANK_DATA["kbo"]
    else:
        title = "⚽ K리그 1 실시간 순위 현황"
        rank_list = REALTIME_RANK_DATA["kleague"]

    embed = discord.Embed(title=title, color=0x2b90d9)
    embed.add_field(name="🏆 순위표", value=rank_list, inline=False)
    embed.set_footer(text="WDS 스포츠 안내 봇 | 실시간 데이터 동기화 완료")
    await interaction.followup.send(embed=embed)


bot.run('MTU1NjI0MjM3MTcyMzc4ODI5OA.GqJx5C.6cc44rZYObl4ej0XqQrT7lu-oX6yeHQVC1B-6k
')
