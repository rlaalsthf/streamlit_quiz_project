import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="🎬 영화관 좌석 추천",
    page_icon="🎬",
    layout="centered"
)

# ── 학번 / 이름 (첫 화면 필수 표시) ─────────────────────────
STUDENT_ID = "2025404058"   # ← 본인 학번으로 변경
STUDENT_NAME = "김민솔"   # ← 본인 이름으로 변경

# ── 사용자 DB (로그인용) ─────────────────────────────────────
USERS = {
    "user123": "pass1234",
    "test":  "test0000",
}

# ── 캐싱: 퀴즈 데이터 로딩 ───────────────────────────────────
# questions.json은 앱 실행 중 변경되지 않으므로 캐싱하여
# 매 렌더링마다 파일을 다시 읽는 I/O 비용을 제거합니다.
@st.cache_data
def load_questions():
    # ▼ 데모 영상용: 터미널에서 이 메시지가 최초 1회만 출력되는 걸 보여주세요
    import time
    print("[캐싱 데모] load_questions() 실제 실행! 이 메시지는 최초 1회만 출력됩니다.")
    time.sleep(0.5)  # 캐싱 효과 체감용 인위적 지연 (영상 촬영 후 삭제)
    # ▲ 데모 영상용 끝
    path = Path(__file__).parent / "data" / "questions.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ── 세션 초기화 ──────────────────────────────────────────────
def init_session():
    defaults = {
        "logged_in": False,
        "username": "",
        "page": "login",        # login | theater | quiz | result
        "theater": None,
        "answers": {},          # {q_id: option_index}
        "current_q": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()
# ── 캐싱 시연용: 로딩 카운터 ────────────────────────────────
# session_state로 렌더링 횟수를 세고,
# load_questions()가 최초 1회만 실제 실행됨을 화면에서 보여줍니다.
if "render_count" not in st.session_state:
    st.session_state.render_count = 0
st.session_state.render_count += 1

data = load_questions()
questions = data["questions"]
theaters  = data["theaters"]

# ── 공통 헤더 ────────────────────────────────────────────────
def show_header():
    st.markdown(
        f"<p style='color:gray;font-size:18px;margin-bottom:0'>"
        f"학번: {STUDENT_ID} &nbsp;|&nbsp; 이름: {STUDENT_NAME}</p>",
        unsafe_allow_html=True
    )
    st.title("🎬 영화관 맞춤 좌석 추천")
    st.divider()

# ════════════════════════════════════════════════════════════
# 1. 로그인 페이지
# ════════════════════════════════════════════════════════════
def page_login():
    show_header()
    st.subheader("로그인")
    st.caption("아이디와 비밀번호를 입력하세요.")

    with st.form("login_form"):
        uid = st.text_input("아이디")
        pwd = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인", use_container_width=True)

    if submitted:
        if uid in USERS and USERS[uid] == pwd:
            st.session_state.logged_in = True
            st.session_state.username  = uid
            st.session_state.page      = "theater"
            st.rerun()
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    st.caption("테스트 계정: `user123` / `pass1234`")

# ════════════════════════════════════════════════════════════
# 2. 특별관 선택 페이지
# ══════════════════════════════════════════════════════
def page_theater():
    show_header()
    st.subheader(f"안녕하세요, {st.session_state.username}님! 👋")
    st.write("오늘 관람할 **특별관**을 선택해 주세요.")

    theater_list = list(theaters.keys())
    theater_icons = {"IMAX": "🖥️", "4DX": "💺", "돌비 시네마": "🔊", "ScreenX": "📽️", "리클라이너": "🛋️", "일반관": "🎦"}

    cols = st.columns(3)
    for i, t in enumerate(theater_list):
        with cols[i % 3]:
            icon = theater_icons.get(t, "🎬")
            if st.button(f"{icon} {t}", use_container_width=True, key=f"th_{t}"):
                st.session_state.theater   = t
                st.session_state.answers   = {}
                st.session_state.current_q = 0
                st.session_state.page      = "quiz"
                st.rerun()

# ════════════════════════════════════════════════════════════
# 3. 퀴즈 페이지 (12문항 순차 진행)
# ════════════════════════════════════════════════════════════
def page_quiz():
    show_header()
    total = len(questions)
    idx   = st.session_state.current_q

    # 진행 상황 표시
    st.caption(f"선택 특별관: **{st.session_state.theater}**")
    st.progress((idx) / total, text=f"{idx} / {total} 완료")
    st.write("")

    if idx >= total:
        st.session_state.page = "result"
        st.rerun()
        return

    q = questions[idx]
    st.markdown(f"### Q{q['id']}. [{q['category']}]")
    st.markdown(f"**{q['question']}**")
    st.write("")

    for i, opt in enumerate(q["options"]):
        if st.button(f"{'ABC'[i]}. {opt['text']}", key=f"q{q['id']}_opt{i}", use_container_width=True):
            st.session_state.answers[q["id"]] = i
            st.session_state.current_q += 1
            st.rerun()

    # 이전 문항으로 돌아가기
    if idx > 0:
        st.write("")
        if st.button("← 이전 문항", key="prev"):
            st.session_state.current_q -= 1
            st.rerun()

# ════════════════════════════════════════════════════════════
# 4. 결과 페이지
# ════════════════════════════════════════════════════════════
# 캐싱: 점수 계산
# 결과 페이지에서 버튼 클릭 등으로 렌더링이 반복될 때
# 동일한 답변 조합이면 12문항 × 4개 점수를 재계산하지 않고
# 캐시에 저장된 결과를 바로 꺼내 씁니다.
# st.cache_data는 dict를 인자로 받을 수 없어서(변경 가능한 타입이라)
# answers를 tuple로 변환해서 넘깁니다.
@st.cache_data
def calc_scores_cached(answers_tuple):
    """(q_id, option_index) 튜플 목록으로 좌석 유형별 점수 합산."""
    answers_dict = dict(answers_tuple)
    totals = {"front": 0, "middle": 0, "back": 0, "aisle": 0}
    for q in questions:
        ans_idx = answers_dict.get(q["id"])
        if ans_idx is not None:
            for seat_type, val in q["options"][ans_idx]["scores"].items():
                totals[seat_type] += val
    return totals

def calc_scores():
    """session_state의 answers를 tuple로 변환해 캐싱 함수에 전달."""
    answers_tuple = tuple(sorted(st.session_state.answers.items()))
    return calc_scores_cached(answers_tuple)

def recommend_seat(scores, theater_name):
    """점수 기반으로 최적 좌석 구역 추천."""
    zone_map = {"front": "앞열", "middle": "중앙열", "back": "뒷열", "aisle": "통로석"}
    best_zone_key = max(scores, key=scores.get)
    theater_info  = theaters[theater_name]
    zone_detail   = theater_info["zones"][best_zone_key]
    return best_zone_key, zone_map[best_zone_key], zone_detail["description"]

def draw_radar(scores):
    """카테고리별 점수 레이더 차트."""
    labels = ["앞열\n(몰입)", "중앙열\n(균형)", "뒷열\n(여유)", "통로석\n(자유)"]
    values = [scores["front"], scores["middle"], scores["back"], scores["aisle"]]
    values_closed = values + [values[0]]
    labels_closed = labels + [labels[0]]

    fig = go.Figure(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(99,110,250,0.3)",
        line=dict(color="rgba(99,110,250,1)", width=2),
        name="좌석 성향"
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(values) + 1])),
        showlegend=False,
        height=350,
        margin=dict(l=40, r=40, t=40, b=40),
    )
    return fig

def draw_bar(scores):
    """좌석 유형별 점수 막대그래프."""
    label_map = {"front": "앞열", "middle": "중앙열", "back": "뒷열", "aisle": "통로석"}
    df = pd.DataFrame({
        "좌석 구역": [label_map[k] for k in scores],
        "점수": list(scores.values())
    })
    fig = px.bar(
        df, x="좌석 구역", y="점수",
        color="좌석 구역",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        text="점수"
    )
    fig.update_layout(showlegend=False, height=300, margin=dict(l=20, r=20, t=20, b=20))
    fig.update_traces(textposition="outside")
    return fig

# 캐싱: 좌석 배치도 시각화
# IMAX 기준 15행 × 20열 = 300개 좌석을 순회하며 Plotly 객체를 만드는
# 연산을 캐싱합니다. theater_name과 best_zone_key가 같으면
# 재생성 없이 저장된 figure를 바로 반환합니다.
@st.cache_data
def draw_seat_map(theater_name, best_zone_key):
    """좌석 배치도 시각화 (추천 구역 강조)."""
    t_info = theaters[theater_name]
    rows   = t_info["seat_map"]["rows"]
    cols   = t_info["seat_map"]["cols"]
    zones  = t_info["zones"]

    front_range  = range(zones["front"]["row_range"][0],  zones["front"]["row_range"][1]  + 1)
    middle_range = range(zones["middle"]["row_range"][0], zones["middle"]["row_range"][1] + 1)
    back_range   = range(zones["back"]["row_range"][0],   zones["back"]["row_range"][1]   + 1)
    aisle_cols   = zones["aisle"]["cols"]

    zone_color = {
        "front":  "#6366f1",
        "middle": "#06b6d4",
        "back":   "#10b981",
        "aisle":  "#f59e0b",
    }
    default_color = "#e5e7eb"
    highlight_color = zone_color[best_zone_key]

    z_data  = []
    hover   = []
    for r in range(1, rows + 1):
        row_z = []
        row_h = []
        for c in range(1, cols + 1):
            if r in front_range:
                zone_key = "front"
                label = "앞열"
            elif r in middle_range:
                zone_key = "middle"
                label = "중앙열"
            else:
                zone_key = "back"
                label = "뒷열"

            if c in aisle_cols:
                zone_key = "aisle"
                label = "통로석"

            is_best = zone_key == best_zone_key
            row_z.append(2 if is_best else 1)
            row_h.append(f"{r}행 {c}열<br>구역: {label}{'  ⭐ 추천' if is_best else ''}")
        z_data.append(row_z)
        hover.append(row_h)

    color_scale = [
        [0.0, default_color],
        [0.5, default_color],
        [0.5, highlight_color],
        [1.0, highlight_color],
    ]

    fig = go.Figure(go.Heatmap(
        z=z_data,
        hovertext=hover,
        hovertemplate="%{hovertext}<extra></extra>",
        colorscale=color_scale,
        showscale=False,
        xgap=2, ygap=2,
    ))

    fig.add_annotation(
        x=cols / 2 - 0.5, y=-1.2,
        text="🎬 스크린",
        showarrow=False,
        font=dict(size=14, color="gray"),
    )

    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=30, b=40),
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False, autorange="reversed"),
        plot_bgcolor="white",
    )
    return fig

def page_result():
    show_header()
    scores = calc_scores()
    best_zone_key, best_zone_label, best_zone_desc = recommend_seat(scores, st.session_state.theater)

    zone_emoji = {"front": "🔥", "middle": "⭐", "back": "🌿", "aisle": "🚪"}

    st.subheader(f"📊 {st.session_state.username}님의 관람 성향 분석 결과")
    st.caption(f"선택 특별관: **{st.session_state.theater}**")
    st.write("")

    # 추천 결과 강조 박스
    st.success(
        f"{zone_emoji.get(best_zone_key, '🎬')} **추천 좌석: {best_zone_label}**\n\n"
        f"{best_zone_desc}"
    )
    st.write("")

    # ── 탭으로 결과 구분 ─────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📊 성향 차트", "🗺️ 좌석 배치도", "📋 내 답변 요약"])

    with tab1:
        st.markdown("#### 좌석 유형별 성향 점수")
        st.markdown("**성향 레이더 차트**")
        st.caption("넓을수록 해당 좌석 유형 선호도가 높아요")
        st.plotly_chart(draw_radar(scores), use_container_width=True)

        st.write("")
        st.write("")

        st.markdown("**좌석 구역별 점수**")
        st.caption("가장 높은 구역이 추천 좌석입니다")
        st.plotly_chart(draw_bar(scores), use_container_width=True)

        # 점수 상세 표
        st.divider()
        st.markdown("**점수 상세**")
        label_map = {"front": "🔥 앞열", "middle": "⭐ 중앙열", "back": "🌿 뒷열", "aisle": "🚪 통로석"}
        score_data = {label_map[k]: [v] for k, v in scores.items()}
        import pandas as pd
        st.dataframe(pd.DataFrame(score_data), use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("#### 좌석 배치도")
        st.caption(f"강조된 구역 = 추천 좌석 ({best_zone_label})")
        st.plotly_chart(draw_seat_map(st.session_state.theater, best_zone_key), use_container_width=True)

        # 구역 설명
        theater_info = theaters[st.session_state.theater]
        st.markdown("**구역별 설명**")
        zone_label_map = {"front": "🔥 앞열", "middle": "⭐ 중앙열", "back": "🌿 뒷열", "aisle": "🚪 통로석"}
        for zk, zv in theater_info["zones"].items():
            prefix = "👉 **추천!** " if zk == best_zone_key else ""
            st.markdown(f"- {zone_label_map[zk]}: {prefix}{zv['description']}")

    with tab3:
        st.markdown("#### 내가 선택한 답변")
        for q in questions:
            ans_idx = st.session_state.answers.get(q["id"])
            if ans_idx is not None:
                opt_text = q["options"][ans_idx]["text"]
                st.markdown(f"**Q{q['id']}. [{q['category']}]** {q['question']}")
                st.markdown(f"> {'ABC'[ans_idx]}. {opt_text}")
                st.write("")

    # 다시 하기
    st.write("")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔄 다른 특별관으로 다시 하기", use_container_width=True):
            st.session_state.page      = "theater"
            st.session_state.answers   = {}
            st.session_state.current_q = 0
            st.rerun()
    with col_b:
        if st.button("🚪 로그아웃", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ════════════════════════════════════════════════════════════
# 사이드바: 설문 안내 + 캐싱 데모
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎬 이용 안내")
    st.divider()

    st.markdown("### 📋 설문 구성")
    st.markdown("""
이 앱은 **12가지 질문**으로 당신의 영화 관람 성향을 분석합니다.

| 카테고리 | 문항 |
|---|---|
| 몰입감 | Q1 |
| 거리감 | Q2 |
| 피로도 | Q3 |
| 음향 | Q4 |
| 환경 | Q5 |
| 집중 스타일 | Q6 |
| 동행자 | Q7 |
| 시각 민감도 | Q8 |
| 취식 및 이동 | Q9 |
| 관람 목적 | Q10 |
| 감정 이입 | Q11 |
| 공간의 여유 | Q12 |
    """)

    st.divider()
    st.markdown("### 🏆 점수 계산 방식")
    st.markdown("""
각 선택지에는 4가지 좌석 유형별 **가산점**이 숨겨져 있어요.

- 🔥 **앞열** — 몰입감 중시
- ⭐ **중앙열** — 균형 중시
- 🌿 **뒷열** — 여유 중시
- 🚪 **통로석** — 이동 편의 중시

12문항 합산 후 **가장 높은 유형**을 추천합니다!
    """)

    st.divider()
    st.markdown("### 🎭 지원 특별관")
    st.markdown("""
- 🖥️ IMAX
- 💺 4DX
- 🔊 돌비 시네마
- 📽️ ScreenX
- 🛋️ 리클라이너
- 🎦 일반관
    """)

    st.divider()
    st.markdown("### 🔧 캐싱 시연 패널")
    st.caption("데모 영상 촬영용")
    st.metric(
        label="앱 전체 렌더링 횟수",
        value=f"{st.session_state.render_count}회",
        help="버튼 클릭 등 인터랙션마다 +1"
    )
    st.info(
        "**캐싱 적용 위치 3곳**\n\n"
        "1️⃣ `load_questions()` - JSON 파일 읽기\n\n"
        "2️⃣ `calc_scores_cached()` - 점수 계산\n\n"
        "3️⃣ `draw_seat_map()` - 좌석 배치도 생성\n\n"
        "👉 렌더링 횟수가 올라가도 터미널 메시지는 최초 1회만 출력됩니다!"
    )
    if st.button("🔄 렌더링 강제 발생 (캐싱 확인용)", use_container_width=True):
        st.rerun()

# ════════════════════════════════════════════════════════════
# 라우터
# ════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    page_login()
else:
    page = st.session_state.page
    if page == "theater":
        page_theater()
    elif page == "quiz":
        page_quiz()
    elif page == "result":
        page_result()
    else:
        page_login()