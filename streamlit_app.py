import streamlit as st
import pandas as pd

from simulation.simulator import run_simulation, PRODUCTS, EVENTS, DAYS

st.set_page_config(
    page_title="학교 매점 모의투자",
    layout="wide",
)

# --- 세션 상태 초기화 ---
if "initialized" not in st.session_state:
    df = run_simulation()
    st.session_state.df = df
    st.session_state.day = 1
    st.session_state.cash = 1_000_000
    st.session_state.holdings = {p: 0 for p in PRODUCTS}
    st.session_state.history = []
    st.session_state.show_event_notice = True  # 첫날 이벤트 팝업 표시
    st.session_state.initialized = True

df = st.session_state.df
day = st.session_state.day
cash = st.session_state.cash
holdings = st.session_state.holdings
history = st.session_state.history

# 오늘 가격 가져오기
today_rows = df[df["day"] == day]
price_map = {row["product"]: float(row["price_end"]) for _, row in today_rows.iterrows()}

# 포트폴리오 가치 계산
portfolio_value = sum(holdings[p] * price_map[p] for p in PRODUCTS)
total_value = cash + portfolio_value

event = EVENTS.get(day, {"code": "일반일", "title": "일반적인 수업일", "desc": ""})

# --- 상단 헤더 / 요약 (KRX 느낌) ---
st.markdown(
    """
    <div style="background-color:#003b8e;padding:12px 20px;border-radius:4px;">
      <span style="color:white;font-weight:700;font-size:20px;">KRX 스타일 · 학교 매점 모의투자</span>
      <span style="color:#d9e4ff;font-size:13px;margin-left:10px;">교육용 모의투자 시뮬레이터</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**현재 일자**")
    st.metric(
        label=f"총 {DAYS}일 중",
        value=f"{day} 일차",
        delta=event["code"]
    )
with col2:
    st.markdown("**전체 자산**")
    st.metric("현금 + 평가금액", f"{int(total_value):,} 원")
with col3:
    st.markdown("**보유 현금**")
    st.metric("매수 가능 금액", f"{int(cash):,} 원")

st.write("---")

# --- 오늘의 이벤트 팝업 느낌 (알림 박스) ---
if st.session_state.get("show_event_notice", False):
    with st.container():
        st.info(f"📢 오늘의 이벤트: **{event['title']}**\n\n{event['desc']}")
        if st.button("이벤트 안내 닫기", key=f"close_evt_{day}"):
            st.session_state.show_event_notice = False

# --- 메인 레이아웃: 왼쪽 주문 테이블 / 오른쪽 이벤트 설명 ---
left, right = st.columns([2, 1])

with left:
    st.subheader("📊 종목 주문 (매수 / 매도)")

    header_cols = st.columns([2, 2, 2, 2, 1, 2, 1])
    for c, title in zip(
        header_cols,
        ["종목명", "현재가", "보유수량", "매수 수량", "매수", "매도 수량", "매도"],
    ):
        c.markdown(f"**{title}**")

    for product in PRODUCTS.keys():
        c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 2, 2, 2, 1, 2, 1])
        price = price_map[product]
        holding = holdings[product]

        with c1:
            st.write(product)
        with c2:
            st.write(f"{price:,.2f}")
        with c3:
            st.write(f"{holding}")
        with c4:
            buy_qty = st.number_input(
                " ",
                min_value=1,
                max_value=1000,
                value=1,
                step=1,
                key=f"buy_qty_{product}_{day}",
            )
        with c5:
            if st.button("매수", key=f"buy_btn_{product}_{day}"):
                cost = price * buy_qty
                if cash >= cost:
                    st.session_state.cash -= cost
                    st.session_state.holdings[product] += buy_qty
                    st.session_state.history.append(
                        {
                            "day": day,
                            "product": product,
                            "side": "매수",
                            "qty": int(buy_qty),
                            "price": price,
                            "amount": cost,
                        }
                    )
                    st.success(f"{product} {int(buy_qty)}개 매수 완료!")
                else:
                    st.error("현금이 부족합니다.")
        with c6:
            sell_qty = st.number_input(
                "  ",
                min_value=1,
                max_value=1000,
                value=1,
                step=1,
                key=f"sell_qty_{product}_{day}",
            )
        with c7:
            if st.button("매도", key=f"sell_btn_{product}_{day}"):
                if holding >= sell_qty:
                    revenue = price * sell_qty
                    st.session_state.cash += revenue
                    st.session_state.holdings[product] -= sell_qty
                    st.session_state.history.append(
                        {
                            "day": day,
                            "product": product,
                            "side": "매도",
                            "qty": int(sell_qty),
                            "price": price,
                            "amount": revenue,
                        }
                    )
                    st.success(f"{product} {int(sell_qty)}개 매도 완료!")
                else:
                    st.error("보유 수량이 부족합니다.")

with right:
    st.subheader("📢 오늘의 이벤트 안내")
    st.markdown(f"**[{event['code']}] {event['title']}**")
    st.write(event["desc"])

    st.write("---")
    st.markdown("**📌 이용 방법**")
    st.markdown(
        """
        1. 각 종목의 **매수/매도 수량**을 입력하고 버튼을 눌러 거래합니다.  
        2. 아래의 **다음 날 ▶** 버튼으로 날짜를 이동하며 30일간 투자합니다.  
        3. 이벤트 상황(시험, 체험학습, 축제 등)에 따라 가격과 수요가 달라집니다.  
        """
    )

st.write("---")

# --- 하단: 다음 날 / 초기화 버튼 ---
c_prev, c_next, c_reset = st.columns([1, 1, 1])
with c_prev:
    st.write(" ")
with c_next:
    if st.button("다음 날 ▶", use_container_width=True):
        if day < DAYS:
            st.session_state.day += 1
            st.session_state.show_event_notice = True
        else:
            st.warning("마지막 날입니다!")
with c_reset:
    if st.button("처음부터 다시", use_container_width=True):
        df = run_simulation()
        st.session_state.df = df
        st.session_state.day = 1
        st.session_state.cash = 1_000_000
        st.session_state.holdings = {p: 0 for p in PRODUCTS}
        st.session_state.history = []
        st.session_state.show_event_notice = True
        st.success("초기화 완료!")

st.write("---")

# --- 주문 내역 테이블 ---
st.subheader("🧾 주문 내역")
if history:
    hist_df = pd.DataFrame(history)
    hist_df = hist_df[["day", "product", "side", "qty", "price", "amount"]]
    hist_df = hist_df.sort_values(["day"]).reset_index(drop=True)
    st.dataframe(hist_df, use_container_width=True)
else:
    st.info("아직 주문한 내역이 없습니다.")
