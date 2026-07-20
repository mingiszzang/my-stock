from datetime import datetime
import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf


# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    page_title="AI 반도체 주식 분석",
    page_icon="🧠",
    layout="wide",
)


# =========================================================
# AI 반도체 종목 데이터베이스
# =========================================================
AI_SEMICONDUCTOR_STOCKS = {
    "AI 가속기·GPU": {
        "NVIDIA": {
            "ticker": "NVDA",
            "country": "미국",
            "currency": "USD",
            "description": "GPU 및 AI 가속기",
        },
        "AMD": {
            "ticker": "AMD",
            "country": "미국",
            "currency": "USD",
            "description": "CPU, GPU 및 AI 가속기",
        },
        "Broadcom": {
            "ticker": "AVGO",
            "country": "미국",
            "currency": "USD",
            "description": "AI 네트워크 및 주문형 반도체",
        },
        "Marvell Technology": {
            "ticker": "MRVL",
            "country": "미국",
            "currency": "USD",
            "description": "데이터센터 네트워크 및 주문형 반도체",
        },
    },
    "파운드리·반도체 제조": {
        "TSMC": {
            "ticker": "TSM",
            "country": "대만",
            "currency": "USD",
            "description": "첨단 반도체 위탁생산",
        },
        "삼성전자": {
            "ticker": "005930.KS",
            "country": "한국",
            "currency": "KRW",
            "description": "메모리, 파운드리 및 시스템 반도체",
        },
        "Intel": {
            "ticker": "INTC",
            "country": "미국",
            "currency": "USD",
            "description": "CPU 및 반도체 제조",
        },
        "GlobalFoundries": {
            "ticker": "GFS",
            "country": "미국",
            "currency": "USD",
            "description": "반도체 위탁생산",
        },
    },
    "HBM·메모리": {
        "SK하이닉스": {
            "ticker": "000660.KS",
            "country": "한국",
            "currency": "KRW",
            "description": "HBM 및 DRAM",
        },
        "Micron Technology": {
            "ticker": "MU",
            "country": "미국",
            "currency": "USD",
            "description": "DRAM, NAND 및 HBM",
        },
        "삼성전자": {
            "ticker": "005930.KS",
            "country": "한국",
            "currency": "KRW",
            "description": "DRAM, NAND 및 HBM",
        },
    },
    "반도체 장비": {
        "ASML": {
            "ticker": "ASML",
            "country": "네덜란드",
            "currency": "USD",
            "description": "EUV 노광장비",
        },
        "Applied Materials": {
            "ticker": "AMAT",
            "country": "미국",
            "currency": "USD",
            "description": "반도체 증착 및 식각 장비",
        },
        "Lam Research": {
            "ticker": "LRCX",
            "country": "미국",
            "currency": "USD",
            "description": "식각 및 증착 장비",
        },
        "KLA": {
            "ticker": "KLAC",
            "country": "미국",
            "currency": "USD",
            "description": "반도체 공정 검사 및 계측",
        },
        "Tokyo Electron": {
            "ticker": "8035.T",
            "country": "일본",
            "currency": "JPY",
            "description": "반도체 제조장비",
        },
    },
    "EDA·반도체 설계 IP": {
        "Synopsys": {
            "ticker": "SNPS",
            "country": "미국",
            "currency": "USD",
            "description": "반도체 설계 자동화 및 IP",
        },
        "Cadence Design Systems": {
            "ticker": "CDNS",
            "country": "미국",
            "currency": "USD",
            "description": "반도체 설계 자동화",
        },
        "Arm Holdings": {
            "ticker": "ARM",
            "country": "영국",
            "currency": "USD",
            "description": "CPU 설계 IP",
        },
    },
    "AI 서버·네트워크": {
        "Super Micro Computer": {
            "ticker": "SMCI",
            "country": "미국",
            "currency": "USD",
            "description": "AI 서버 및 데이터센터 시스템",
        },
        "Arista Networks": {
            "ticker": "ANET",
            "country": "미국",
            "currency": "USD",
            "description": "AI 데이터센터 네트워크",
        },
        "Dell Technologies": {
            "ticker": "DELL",
            "country": "미국",
            "currency": "USD",
            "description": "AI 서버 및 인프라",
        },
    },
}


BENCHMARKS = {
    "필라델피아 반도체지수": "^SOX",
    "NASDAQ 종합지수": "^IXIC",
    "S&P 500": "^GSPC",
    "KOSPI": "^KS11",
}


PERIOD_OPTIONS = {
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "연초 이후": "ytd",
    "1년": "1y",
    "2년": "2y",
    "5년": "5y",
}


CURRENCY_SYMBOLS = {
    "USD": "$",
    "KRW": "₩",
    "JPY": "¥",
    "EUR": "€",
    "GBP": "£",
    "TWD": "NT$",
}


# =========================================================
# 종목 목록 정리
# =========================================================
def build_stock_database():
    database = {}

    for category, stocks in AI_SEMICONDUCTOR_STOCKS.items():
        for company, information in stocks.items():
            ticker = information["ticker"]

            if ticker not in database:
                database[ticker] = {
                    "company": company,
                    "ticker": ticker,
                    "country": information["country"],
                    "currency": information["currency"],
                    "description": information["description"],
                    "categories": [category],
                }
            elif category not in database[ticker]["categories"]:
                database[ticker]["categories"].append(category)

    return database


STOCK_DATABASE = build_stock_database()


# =========================================================
# Yahoo Finance 데이터 조회
# =========================================================
@st.cache_data(ttl=1800, show_spinner=False)
def download_stock_data(ticker, period, interval="1d"):
    """
    Yahoo Finance 데이터를 조회합니다.

    1차: yf.download()
    2차: Ticker.history()
    """

    data = pd.DataFrame()

    try:
        data = yf.download(
            tickers=ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
            timeout=20,
        )
    except Exception:
        data = pd.DataFrame()

    if data is None or data.empty:
        try:
            ticker_object = yf.Ticker(ticker)

            data = ticker_object.history(
                period=period,
                interval=interval,
                auto_adjust=False,
                timeout=20,
            )
        except Exception:
            return pd.DataFrame()

    if data is None or data.empty:
        return pd.DataFrame()

    data = data.copy()

    # 단일 티커임에도 MultiIndex가 반환되는 경우 처리
    if isinstance(data.columns, pd.MultiIndex):
        first_level = data.columns.get_level_values(0)
        last_level = data.columns.get_level_values(-1)

        if ticker in last_level:
            try:
                data = data.xs(
                    ticker,
                    axis=1,
                    level=-1,
                    drop_level=True,
                )
            except Exception:
                data.columns = first_level
        else:
            data.columns = first_level

    data.index = pd.to_datetime(data.index)

    if getattr(data.index, "tz", None) is not None:
        data.index = data.index.tz_localize(None)

    required_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    for column in required_columns:
        if column not in data.columns:
            data[column] = pd.NA

    if "Adj Close" not in data.columns:
        data["Adj Close"] = data["Close"]

    numeric_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
        "Volume",
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

    data = data.dropna(subset=["Close"])

    return data


def load_multiple_stocks(stock_items, period):
    loaded_data = {}
    failed_tickers = []

    progress_bar = st.progress(0)
    progress_text = st.empty()

    total_count = len(stock_items)

    for index, item in enumerate(stock_items):
        company = item["company"]
        ticker = item["ticker"]

        progress_text.caption(
            f"데이터 조회 중: {company} ({ticker})"
        )

        data = download_stock_data(
            ticker=ticker,
            period=period,
            interval="1d",
        )

        if data.empty:
            failed_tickers.append(ticker)
        else:
            loaded_data[ticker] = {
                "information": item,
                "data": data,
            }

        progress_bar.progress((index + 1) / total_count)

        # Yahoo Finance에 지나치게 빠른 연속 요청 방지
        time.sleep(0.05)

    progress_bar.empty()
    progress_text.empty()

    return loaded_data, failed_tickers


# =========================================================
# 기술적 지표 계산
# =========================================================
def add_technical_indicators(data):
    result = data.copy()

    price = result["Adj Close"]

    # 이동평균
    result["MA20"] = price.rolling(window=20).mean()
    result["MA60"] = price.rolling(window=60).mean()
    result["MA120"] = price.rolling(window=120).mean()

    # 볼린저밴드
    result["BB_Middle"] = price.rolling(window=20).mean()
    rolling_std = price.rolling(window=20).std()

    result["BB_Upper"] = result["BB_Middle"] + 2 * rolling_std
    result["BB_Lower"] = result["BB_Middle"] - 2 * rolling_std

    # RSI 14
    price_change = price.diff()

    gain = price_change.clip(lower=0)
    loss = -price_change.clip(upper=0)

    average_gain = gain.ewm(
        alpha=1 / 14,
        adjust=False,
        min_periods=14,
    ).mean()

    average_loss = loss.ewm(
        alpha=1 / 14,
        adjust=False,
        min_periods=14,
    ).mean()

    relative_strength = average_gain / average_loss.replace(0, pd.NA)

    result["RSI"] = 100 - (
        100 / (1 + relative_strength)
    )

    # MACD
    ema12 = price.ewm(
        span=12,
        adjust=False,
    ).mean()

    ema26 = price.ewm(
        span=26,
        adjust=False,
    ).mean()

    result["MACD"] = ema12 - ema26
    result["MACD_Signal"] = result["MACD"].ewm(
        span=9,
        adjust=False,
    ).mean()

    result["MACD_Histogram"] = (
        result["MACD"] - result["MACD_Signal"]
    )

    # 일간 수익률
    result["Daily_Return"] = price.pct_change()

    return result


# =========================================================
# 성과 지표 계산
# =========================================================
def safe_period_return(price, trading_days):
    if price is None or price.empty:
        return None

    if len(price) <= trading_days:
        return None

    base_price = price.iloc[-trading_days - 1]

    if base_price == 0:
        return None

    return (price.iloc[-1] / base_price - 1) * 100


def calculate_max_drawdown(price):
    if price is None or price.empty:
        return None

    cumulative_peak = price.cummax()
    drawdown = price / cumulative_peak - 1

    return drawdown.min() * 100


def calculate_stock_metrics(data):
    price = data["Adj Close"].dropna()

    if price.empty:
        return {}

    daily_returns = price.pct_change().dropna()

    current_price = price.iloc[-1]

    previous_price = (
        price.iloc[-2]
        if len(price) >= 2
        else current_price
    )

    daily_change = (
        (current_price / previous_price - 1) * 100
        if previous_price != 0
        else None
    )

    period_return = (
        (current_price / price.iloc[0] - 1) * 100
        if price.iloc[0] != 0
        else None
    )

    annual_volatility = (
        daily_returns.std() * (252 ** 0.5) * 100
        if not daily_returns.empty
        else None
    )

    annual_return = (
        daily_returns.mean() * 252 * 100
        if not daily_returns.empty
        else None
    )

    downside_returns = daily_returns[
        daily_returns < 0
    ]

    downside_deviation = (
        downside_returns.std() * (252 ** 0.5)
        if not downside_returns.empty
        else None
    )

    sortino_ratio = None

    if (
        downside_deviation is not None
        and downside_deviation != 0
        and not daily_returns.empty
    ):
        sortino_ratio = (
            daily_returns.mean() * 252
        ) / downside_deviation

    return {
        "current_price": current_price,
        "daily_change": daily_change,
        "period_return": period_return,
        "return_1m": safe_period_return(price, 21),
        "return_3m": safe_period_return(price, 63),
        "return_6m": safe_period_return(price, 126),
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "max_drawdown": calculate_max_drawdown(price),
        "sortino_ratio": sortino_ratio,
        "period_high": price.max(),
        "period_low": price.min(),
    }


def calculate_momentum_score(metrics, technical_data):
    """
    가격 모멘텀과 위험지표를 이용한 단순 비교점수입니다.

    투자 추천이나 목표주가가 아니라,
    선택된 종목 사이의 상대 비교용 지표입니다.
    """

    score = 50.0

    return_1m = metrics.get("return_1m")
    return_3m = metrics.get("return_3m")
    return_6m = metrics.get("return_6m")
    volatility = metrics.get("annual_volatility")
    max_drawdown = metrics.get("max_drawdown")

    if return_1m is not None:
        score += max(-10, min(10, return_1m * 0.4))

    if return_3m is not None:
        score += max(-12, min(12, return_3m * 0.25))

    if return_6m is not None:
        score += max(-12, min(12, return_6m * 0.15))

    if volatility is not None:
        if volatility < 30:
            score += 4
        elif volatility > 60:
            score -= 5

    if max_drawdown is not None:
        if max_drawdown > -15:
            score += 4
        elif max_drawdown < -40:
            score -= 6

    latest = technical_data.iloc[-1]

    current_price = latest.get("Adj Close")
    ma20 = latest.get("MA20")
    ma60 = latest.get("MA60")
    rsi = latest.get("RSI")
    macd = latest.get("MACD")
    macd_signal = latest.get("MACD_Signal")

    if pd.notna(current_price) and pd.notna(ma20):
        score += 4 if current_price > ma20 else -4

    if pd.notna(current_price) and pd.notna(ma60):
        score += 4 if current_price > ma60 else -4

    if pd.notna(rsi):
        if 45 <= rsi <= 65:
            score += 3
        elif rsi >= 75:
            score -= 3
        elif rsi <= 30:
            score -= 2

    if pd.notna(macd) and pd.notna(macd_signal):
        score += 3 if macd > macd_signal else -3

    return round(max(0, min(100, score)), 1)


def score_label(score):
    if score >= 75:
        return "강한 모멘텀"
    if score >= 60:
        return "양호"
    if score >= 45:
        return "중립"
    if score >= 30:
        return "약세"
    return "매우 약한 모멘텀"


# =========================================================
# 표시 형식 함수
# =========================================================
def format_number(value, digits=2):
    if value is None or pd.isna(value):
        return "-"

    return f"{value:,.{digits}f}"


def format_percent(value):
    if value is None or pd.isna(value):
        return "-"

    return f"{value:+.2f}%"


def format_ratio(value):
    if value is None or pd.isna(value):
        return "-"

    return f"{value:.2f}"


def currency_symbol(currency):
    return CURRENCY_SYMBOLS.get(
        currency,
        f"{currency} " if currency else "",
    )


def dataframe_to_csv(dataframe):
    return dataframe.to_csv(
        index=True,
    ).encode("utf-8-sig")


# =========================================================
# Plotly 차트
# =========================================================
def create_price_chart(data, company):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Adj Close"],
            mode="lines",
            name="수정주가",
            line=dict(width=2.5),
            hovertemplate=(
                "%{x|%Y-%m-%d}<br>"
                "주가: %{y:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA20"],
            mode="lines",
            name="20일 이동평균",
            line=dict(width=1.5),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA60"],
            mode="lines",
            name="60일 이동평균",
            line=dict(width=1.5),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA120"],
            mode="lines",
            name="120일 이동평균",
            line=dict(width=1.5),
        )
    )

    fig.update_layout(
        title=f"{company} 주가와 이동평균선",
        xaxis_title="날짜",
        yaxis_title="가격",
        height=550,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            orientation="h",
            y=1.02,
            x=1,
            xanchor="right",
            yanchor="bottom",
        ),
    )

    fig.update_xaxes(
        rangeslider_visible=True,
        rangebreaks=[
            dict(bounds=["sat", "mon"]),
        ],
    )

    return fig


def create_bollinger_chart(data, company):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["BB_Upper"],
            mode="lines",
            name="상단밴드",
            line=dict(width=1),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["BB_Lower"],
            mode="lines",
            name="하단밴드",
            line=dict(width=1),
            fill="tonexty",
            fillcolor="rgba(150, 150, 150, 0.12)",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["BB_Middle"],
            mode="lines",
            name="20일 중심선",
            line=dict(width=1.5),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Adj Close"],
            mode="lines",
            name="수정주가",
            line=dict(width=2.5),
        )
    )

    fig.update_layout(
        title=f"{company} 볼린저밴드",
        xaxis_title="날짜",
        yaxis_title="가격",
        height=520,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


def create_candlestick_chart(data, company):
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name=company,
            increasing_line_color="#ef5350",
            decreasing_line_color="#2962ff",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA20"],
            mode="lines",
            name="20일 이동평균",
            line=dict(width=1.5),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA60"],
            mode="lines",
            name="60일 이동평균",
            line=dict(width=1.5),
        )
    )

    fig.update_layout(
        title=f"{company} 캔들스틱",
        xaxis_title="날짜",
        yaxis_title="가격",
        height=600,
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),
        ]
    )

    return fig


def create_volume_chart(data, company):
    volume_data = data.reset_index()
    date_column = volume_data.columns[0]

    fig = px.bar(
        volume_data,
        x=date_column,
        y="Volume",
        title=f"{company} 거래량",
        labels={
            date_column: "날짜",
            "Volume": "거래량",
        },
    )

    fig.update_traces(
        hovertemplate=(
            "%{x|%Y-%m-%d}<br>"
            "거래량: %{y:,.0f}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        height=420,
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


def create_rsi_chart(data, company):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["RSI"],
            mode="lines",
            name="RSI(14)",
        )
    )

    fig.add_hline(
        y=70,
        line_dash="dash",
        annotation_text="과열 기준 70",
    )

    fig.add_hline(
        y=30,
        line_dash="dash",
        annotation_text="과매도 기준 30",
    )

    fig.update_layout(
        title=f"{company} RSI",
        xaxis_title="날짜",
        yaxis_title="RSI",
        yaxis_range=[0, 100],
        height=400,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


def create_macd_chart(data, company):
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data["MACD_Histogram"],
            name="히스토그램",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MACD"],
            mode="lines",
            name="MACD",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MACD_Signal"],
            mode="lines",
            name="시그널",
        )
    )

    fig.add_hline(
        y=0,
        line_dash="dash",
    )

    fig.update_layout(
        title=f"{company} MACD",
        xaxis_title="날짜",
        yaxis_title="MACD",
        height=430,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


def create_normalized_chart(comparison_data):
    long_data = (
        comparison_data
        .reset_index()
        .melt(
            id_vars="Date",
            var_name="종목",
            value_name="정규화 지수",
        )
    )

    fig = px.line(
        long_data,
        x="Date",
        y="정규화 지수",
        color="종목",
        title="AI 반도체 종목 상대수익률 비교",
        labels={
            "Date": "날짜",
            "정규화 지수": "시작일 = 100",
        },
    )

    fig.add_hline(
        y=100,
        line_dash="dash",
        annotation_text="시작점",
    )

    fig.update_layout(
        height=620,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            orientation="h",
            y=1.02,
            x=1,
            xanchor="right",
            yanchor="bottom",
        ),
    )

    return fig


def create_risk_return_chart(summary_data):
    plot_data = summary_data.dropna(
        subset=[
            "연환산 변동성(%)",
            "기간 수익률(%)",
        ]
    ).copy()

    fig = px.scatter(
        plot_data,
        x="연환산 변동성(%)",
        y="기간 수익률(%)",
        size="모멘텀 점수",
        color="밸류체인",
        hover_name="종목",
        hover_data={
            "티커": True,
            "모멘텀 점수": True,
            "연환산 변동성(%)": ":.2f",
            "기간 수익률(%)": ":.2f",
        },
        title="위험·수익률 비교",
        labels={
            "연환산 변동성(%)": "연환산 변동성",
            "기간 수익률(%)": "기간 수익률",
        },
        size_max=45,
    )

    fig.add_hline(
        y=0,
        line_dash="dash",
    )

    fig.update_layout(
        height=600,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


# =========================================================
# 화면 헤더
# =========================================================
st.title("🧠 AI 반도체 주식 전문 분석")

st.caption(
    "AI 가속기, HBM, 파운드리, 반도체 장비, EDA 및 "
    "AI 서버 밸류체인의 주요 종목을 비교합니다."
)

st.warning(
    "이 페이지의 모멘텀 점수는 가격과 기술적 지표를 이용한 "
    "상대 비교용 지표입니다. 기업가치 평가, 목표주가 또는 "
    "매수·매도 추천을 의미하지 않습니다."
)


# =========================================================
# 사이드바 설정
# =========================================================
with st.sidebar:
    st.header("AI 반도체 분석 설정")

    selected_categories = st.multiselect(
        "밸류체인 선택",
        options=list(AI_SEMICONDUCTOR_STOCKS.keys()),
        default=[
            "AI 가속기·GPU",
            "HBM·메모리",
            "반도체 장비",
        ],
    )

    available_items = []

    for ticker, item in STOCK_DATABASE.items():
        if any(
            category in item["categories"]
            for category in selected_categories
        ):
            available_items.append(item)

    label_to_ticker = {
        (
            f"{item['company']} "
            f"({item['ticker']})"
        ): item["ticker"]
        for item in available_items
    }

    default_labels = list(label_to_ticker.keys())[:8]

    selected_labels = st.multiselect(
        "분석 종목",
        options=list(label_to_ticker.keys()),
        default=default_labels,
        help="Yahoo Finance 요청 제한을 고려해 5~10개 정도를 권장합니다.",
    )

    period_label = st.selectbox(
        "분석 기간",
        options=list(PERIOD_OPTIONS.keys()),
        index=4,
    )

    selected_benchmark_name = st.selectbox(
        "비교 지수",
        options=list(BENCHMARKS.keys()),
        index=0,
    )

    include_benchmark = st.checkbox(
        "수익률 비교 차트에 지수 포함",
        value=True,
    )

    st.divider()

    if st.button(
        "화면 다시 그리기",
        use_container_width=True,
        type="primary",
    ):
        st.rerun()

    st.caption(
        "시장 데이터는 30분 동안 캐시됩니다."
    )


# =========================================================
# 사용자 선택 검증
# =========================================================
if not selected_categories:
    st.info("사이드바에서 하나 이상의 밸류체인을 선택해 주세요.")
    st.stop()

if not selected_labels:
    st.info("사이드바에서 하나 이상의 종목을 선택해 주세요.")
    st.stop()


selected_tickers = [
    label_to_ticker[label]
    for label in selected_labels
]

selected_stock_items = [
    STOCK_DATABASE[ticker]
    for ticker in selected_tickers
]

period = PERIOD_OPTIONS[period_label]


# =========================================================
# 데이터 불러오기
# =========================================================
with st.spinner(
    "AI 반도체 종목 데이터를 불러오고 있습니다..."
):
    loaded_data, failed_tickers = load_multiple_stocks(
        selected_stock_items,
        period,
    )


if failed_tickers:
    st.warning(
        "다음 티커의 데이터를 불러오지 못했습니다: "
        + ", ".join(failed_tickers)
        + "\n\n잠시 후 다시 접속하거나 분석 종목 수를 줄여보세요."
    )


if not loaded_data:
    st.error(
        "조회 가능한 종목 데이터가 없습니다. "
        "Yahoo Finance의 일시적인 접속 제한일 수 있습니다."
    )
    st.stop()


# =========================================================
# 기술적 지표와 요약 데이터 생성
# =========================================================
summary_rows = []
technical_data_map = {}

for ticker, item in loaded_data.items():
    information = item["information"]
    raw_data = item["data"]

    technical_data = add_technical_indicators(raw_data)
    technical_data_map[ticker] = technical_data

    metrics = calculate_stock_metrics(technical_data)

    score = calculate_momentum_score(
        metrics,
        technical_data,
    )

    latest_rsi = technical_data["RSI"].iloc[-1]
    latest_macd = technical_data["MACD"].iloc[-1]
    latest_signal = technical_data["MACD_Signal"].iloc[-1]

    summary_rows.append(
        {
            "종목": information["company"],
            "티커": ticker,
            "국가": information["country"],
            "밸류체인": " · ".join(
                information["categories"]
            ),
            "현재가": metrics.get("current_price"),
            "일간 등락률(%)": metrics.get("daily_change"),
            "1개월 수익률(%)": metrics.get("return_1m"),
            "3개월 수익률(%)": metrics.get("return_3m"),
            "6개월 수익률(%)": metrics.get("return_6m"),
            "기간 수익률(%)": metrics.get("period_return"),
            "연환산 변동성(%)": metrics.get("annual_volatility"),
            "최대 낙폭(%)": metrics.get("max_drawdown"),
            "Sortino": metrics.get("sortino_ratio"),
            "RSI": latest_rsi,
            "MACD 상태": (
                "상승"
                if (
                    pd.notna(latest_macd)
                    and pd.notna(latest_signal)
                    and latest_macd > latest_signal
                )
                else "하락"
            ),
            "모멘텀 점수": score,
            "점수 해석": score_label(score),
        }
    )


summary_data = pd.DataFrame(summary_rows)

summary_data = summary_data.sort_values(
    by="모멘텀 점수",
    ascending=False,
).reset_index(drop=True)

summary_data.index = summary_data.index + 1
summary_data.index.name = "순위"


# =========================================================
# 시장 요약
# =========================================================
st.header("📊 AI 반도체 시장 요약")

best_stock = summary_data.iloc[0]

positive_count = (
    summary_data["기간 수익률(%)"] > 0
).sum()

median_return = summary_data[
    "기간 수익률(%)"
].median()

median_volatility = summary_data[
    "연환산 변동성(%)"
].median()

summary_columns = st.columns(4)

with summary_columns[0]:
    st.metric(
        "최고 모멘텀 종목",
        best_stock["종목"],
        f"{best_stock['모멘텀 점수']:.1f}점",
    )

with summary_columns[1]:
    st.metric(
        "상승 종목",
        f"{positive_count} / {len(summary_data)}",
    )

with summary_columns[2]:
    st.metric(
        "수익률 중앙값",
        format_percent(median_return),
    )

with summary_columns[3]:
    st.metric(
        "변동성 중앙값",
        (
            f"{format_number(median_volatility)}%"
            if pd.notna(median_volatility)
            else "-"
        ),
    )


# =========================================================
# 순위표
# =========================================================
ranking_tab, return_tab, risk_tab = st.tabs(
    [
        "종합 순위",
        "수익률 비교",
        "위험·수익률",
    ]
)

with ranking_tab:
    ranking_columns = [
        "종목",
        "티커",
        "밸류체인",
        "일간 등락률(%)",
        "1개월 수익률(%)",
        "3개월 수익률(%)",
        "6개월 수익률(%)",
        "기간 수익률(%)",
        "연환산 변동성(%)",
        "최대 낙폭(%)",
        "RSI",
        "MACD 상태",
        "모멘텀 점수",
        "점수 해석",
    ]

    display_ranking = summary_data[
        ranking_columns
    ].copy()

    numeric_columns = [
        "일간 등락률(%)",
        "1개월 수익률(%)",
        "3개월 수익률(%)",
        "6개월 수익률(%)",
        "기간 수익률(%)",
        "연환산 변동성(%)",
        "최대 낙폭(%)",
        "RSI",
        "모멘텀 점수",
    ]

    for column in numeric_columns:
        display_ranking[column] = (
            display_ranking[column].round(2)
        )

    st.dataframe(
        display_ranking,
        use_container_width=True,
        height=min(
            650,
            60 + len(display_ranking) * 38,
        ),
        column_config={
            "일간 등락률(%)": st.column_config.NumberColumn(
                format="%.2f%%"
            ),
            "1개월 수익률(%)": st.column_config.NumberColumn(
                format="%.2f%%"
            ),
            "3개월 수익률(%)": st.column_config.NumberColumn(
                format="%.2f%%"
            ),
            "6개월 수익률(%)": st.column_config.NumberColumn(
                format="%.2f%%"
            ),
            "기간 수익률(%)": st.column_config.NumberColumn(
                format="%.2f%%"
            ),
            "연환산 변동성(%)": st.column_config.NumberColumn(
                format="%.2f%%"
            ),
            "최대 낙폭(%)": st.column_config.NumberColumn(
                format="%.2f%%"
            ),
            "모멘텀 점수": st.column_config.ProgressColumn(
                min_value=0,
                max_value=100,
                format="%.1f",
            ),
        },
    )

    st.download_button(
        label="AI 반도체 분석 결과 CSV 다운로드",
        data=dataframe_to_csv(display_ranking),
        file_name=(
            "ai_semiconductor_analysis_"
            f"{datetime.now().strftime('%Y%m%d')}.csv"
        ),
        mime="text/csv",
    )

with return_tab:
    normalized_series = {}

    for ticker, technical_data in technical_data_map.items():
        price = technical_data["Adj Close"].dropna()

        if price.empty or price.iloc[0] == 0:
            continue

        company = STOCK_DATABASE[ticker]["company"]

        normalized_series[
            f"{company} ({ticker})"
        ] = price / price.iloc[0] * 100

    if include_benchmark:
        benchmark_ticker = BENCHMARKS[
            selected_benchmark_name
        ]

        benchmark_data = download_stock_data(
            benchmark_ticker,
            period,
            "1d",
        )

        if not benchmark_data.empty:
            benchmark_price = benchmark_data[
                "Adj Close"
            ].dropna()

            if (
                not benchmark_price.empty
                and benchmark_price.iloc[0] != 0
            ):
                normalized_series[
                    selected_benchmark_name
                ] = (
                    benchmark_price
                    / benchmark_price.iloc[0]
                    * 100
                )
        else:
            st.info(
                "선택한 비교 지수의 데이터를 불러오지 못했습니다."
            )

    if normalized_series:
        comparison_data = pd.concat(
            normalized_series,
            axis=1,
        ).sort_index()

        comparison_data.index.name = "Date"

        st.plotly_chart(
            create_normalized_chart(
                comparison_data
            ),
            use_container_width=True,
            config={
                "displaylogo": False,
                "scrollZoom": True,
            },
        )

with risk_tab:
    st.plotly_chart(
        create_risk_return_chart(
            summary_data.reset_index()
        ),
        use_container_width=True,
        config={
            "displaylogo": False,
        },
    )

    st.caption(
        "오른쪽으로 갈수록 가격 변동성이 크고, "
        "위쪽으로 갈수록 선택 기간 수익률이 높습니다."
    )


# =========================================================
# 개별 종목 상세 분석
# =========================================================
st.divider()
st.header("🔍 개별 종목 상세 분석")

detail_options = {
    (
        f"{STOCK_DATABASE[ticker]['company']} "
        f"({ticker})"
    ): ticker
    for ticker in technical_data_map.keys()
}

selected_detail_label = st.selectbox(
    "상세 분석 종목",
    options=list(detail_options.keys()),
)

detail_ticker = detail_options[
    selected_detail_label
]

detail_information = STOCK_DATABASE[
    detail_ticker
]

detail_data = technical_data_map[
    detail_ticker
]

detail_metrics = calculate_stock_metrics(
    detail_data
)

detail_score = calculate_momentum_score(
    detail_metrics,
    detail_data,
)

detail_symbol = currency_symbol(
    detail_information["currency"]
)


st.subheader(
    f"{detail_information['company']} · {detail_ticker}"
)

st.caption(
    f"{detail_information['country']} | "
    f"{' · '.join(detail_information['categories'])} | "
    f"{detail_information['description']}"
)


# =========================================================
# 개별 종목 주요 지표
# =========================================================
metric_columns = st.columns(6)

with metric_columns[0]:
    st.metric(
        "현재가",
        (
            f"{detail_symbol}"
            f"{format_number(detail_metrics['current_price'])}"
        ),
        format_percent(
            detail_metrics["daily_change"]
        ),
    )

with metric_columns[1]:
    st.metric(
        f"{period_label} 수익률",
        format_percent(
            detail_metrics["period_return"]
        ),
    )

with metric_columns[2]:
    st.metric(
        "1개월 수익률",
        format_percent(
            detail_metrics["return_1m"]
        ),
    )

with metric_columns[3]:
    st.metric(
        "연환산 변동성",
        (
            f"{format_number(detail_metrics['annual_volatility'])}%"
            if detail_metrics["annual_volatility"] is not None
            else "-"
        ),
    )

with metric_columns[4]:
    st.metric(
        "최대 낙폭",
        format_percent(
            detail_metrics["max_drawdown"]
        ),
    )

with metric_columns[5]:
    st.metric(
        "모멘텀 점수",
        f"{detail_score:.1f}점",
        score_label(detail_score),
    )


# =========================================================
# 기술적 상태 설명
# =========================================================
latest_row = detail_data.iloc[-1]

current_price = latest_row["Adj Close"]
ma20 = latest_row["MA20"]
ma60 = latest_row["MA60"]
rsi = latest_row["RSI"]
macd = latest_row["MACD"]
macd_signal = latest_row["MACD_Signal"]

technical_messages = []

if pd.notna(ma20):
    technical_messages.append(
        "주가가 20일 이동평균선 위에 있습니다."
        if current_price > ma20
        else "주가가 20일 이동평균선 아래에 있습니다."
    )

if pd.notna(ma60):
    technical_messages.append(
        "중기 추세는 상대적으로 강합니다."
        if current_price > ma60
        else "중기 추세는 상대적으로 약합니다."
    )

if pd.notna(rsi):
    if rsi >= 70:
        technical_messages.append(
            f"RSI는 {rsi:.1f}로 단기 과열 구간에 있습니다."
        )
    elif rsi <= 30:
        technical_messages.append(
            f"RSI는 {rsi:.1f}로 단기 과매도 구간에 있습니다."
        )
    else:
        technical_messages.append(
            f"RSI는 {rsi:.1f}로 중립 범위에 있습니다."
        )

if pd.notna(macd) and pd.notna(macd_signal):
    technical_messages.append(
        "MACD가 시그널선을 상회하고 있습니다."
        if macd > macd_signal
        else "MACD가 시그널선을 하회하고 있습니다."
    )

if technical_messages:
    st.info(" ".join(technical_messages))


# =========================================================
# 개별 종목 차트
# =========================================================
(
    price_tab,
    candle_tab,
    band_tab,
    momentum_tab,
    volume_tab,
    raw_data_tab,
) = st.tabs(
    [
        "주가·이동평균",
        "캔들스틱",
        "볼린저밴드",
        "RSI·MACD",
        "거래량",
        "원본 데이터",
    ]
)

with price_tab:
    st.plotly_chart(
        create_price_chart(
            detail_data,
            detail_information["company"],
        ),
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": True,
        },
    )

with candle_tab:
    st.plotly_chart(
        create_candlestick_chart(
            detail_data,
            detail_information["company"],
        ),
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": True,
        },
    )

with band_tab:
    st.plotly_chart(
        create_bollinger_chart(
            detail_data,
            detail_information["company"],
        ),
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": True,
        },
    )

with momentum_tab:
    st.plotly_chart(
        create_rsi_chart(
            detail_data,
            detail_information["company"],
        ),
        use_container_width=True,
        config={
            "displaylogo": False,
        },
    )

    st.plotly_chart(
        create_macd_chart(
            detail_data,
            detail_information["company"],
        ),
        use_container_width=True,
        config={
            "displaylogo": False,
        },
    )

with volume_tab:
    st.plotly_chart(
        create_volume_chart(
            detail_data,
            detail_information["company"],
        ),
        use_container_width=True,
        config={
            "displaylogo": False,
        },
    )

with raw_data_tab:
    raw_display = detail_data[
        [
            "Open",
            "High",
            "Low",
            "Close",
            "Adj Close",
            "Volume",
            "MA20",
            "MA60",
            "RSI",
            "MACD",
            "MACD_Signal",
        ]
    ].copy()

    raw_display.index = raw_display.index.strftime(
        "%Y-%m-%d"
    )

    raw_display.index.name = "Date"

    st.dataframe(
        raw_display.sort_index(
            ascending=False
        ),
        use_container_width=True,
    )

    st.download_button(
        label=f"{detail_ticker} 가격 데이터 CSV 다운로드",
        data=dataframe_to_csv(raw_display),
        file_name=(
            f"{detail_ticker}_"
            f"{period}_"
            f"{datetime.now().strftime('%Y%m%d')}.csv"
        ),
        mime="text/csv",
    )


# =========================================================
# 분석 방법
# =========================================================
st.divider()

with st.expander("모멘텀 점수 산정 방식"):
    st.markdown(
        """
        모멘텀 점수는 다음 항목을 조합한 0~100점의 상대 비교 지표입니다.

        - 최근 1개월, 3개월 및 6개월 수익률
        - 현재 주가의 20일·60일 이동평균선 상회 여부
        - RSI 수준
        - MACD와 시그널선의 관계
        - 연환산 변동성
        - 최대 낙폭

        종목의 매출, 이익, 밸류에이션, 경쟁력 또는 미래 실적은
        점수에 반영되지 않습니다. 따라서 점수가 높다는 이유만으로
        기업가치가 저평가되었거나 향후 주가가 상승한다는 의미는 아닙니다.
        """
    )


st.info(
    "Yahoo Finance 데이터는 지연되거나 일시적으로 조회되지 않을 수 있습니다. "
    "이 페이지는 교육 및 정보 제공용이며 투자 권유를 목적으로 하지 않습니다."
)
