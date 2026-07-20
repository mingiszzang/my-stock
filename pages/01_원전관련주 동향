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
    page_title="두산에너빌리티 관련주 동향",
    page_icon="⚡",
    layout="wide",
)


# =========================================================
# 종목 데이터베이스
# =========================================================
RELATED_STOCKS = {
    "핵심 종목": {
        "두산에너빌리티": {
            "ticker": "034020.KS",
            "description": "원전 주기기, 가스터빈, 발전 플랜트 및 에너지 솔루션",
        },
    },
    "원전 설계·정비": {
        "한전기술": {
            "ticker": "052690.KS",
            "description": "원전 및 발전소 설계·엔지니어링",
        },
        "한전KPS": {
            "ticker": "051600.KS",
            "description": "원전·화력·송변전 설비 정비",
        },
    },
    "원전 계측·제어": {
        "우진": {
            "ticker": "105840.KS",
            "description": "원전용 계측기기 및 산업용 계측",
        },
        "우리기술": {
            "ticker": "032820.KQ",
            "description": "원전 감시·제어 시스템",
        },
        "오르비텍": {
            "ticker": "046120.KQ",
            "description": "원전 방사선 관리 및 비파괴검사",
        },
    },
    "발전설비·보조기기": {
        "비에이치아이": {
            "ticker": "083650.KQ",
            "description": "발전용 보일러 및 원전 보조기기",
        },
        "SNT에너지": {
            "ticker": "100840.KS",
            "description": "발전·석유화학용 열교환기 및 공랭식 열교환기",
        },
    },
    "전력 인프라": {
        "HD현대일렉트릭": {
            "ticker": "267260.KS",
            "description": "변압기·차단기 등 전력기기",
        },
        "효성중공업": {
            "ticker": "298040.KS",
            "description": "초고압 변압기 및 전력 시스템",
        },
        "LS ELECTRIC": {
            "ticker": "010120.KS",
            "description": "전력·자동화 시스템 및 배전기기",
        },
    },
}


BENCHMARKS = {
    "KOSPI": "^KS11",
    "KOSDAQ": "^KQ11",
    "S&P 500": "^GSPC",
    "필라델피아 반도체지수": "^SOX",
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


# =========================================================
# 종목 목록 생성
# =========================================================
def build_stock_database():
    database = {}

    for category, stocks in RELATED_STOCKS.items():
        for company, information in stocks.items():
            ticker = information["ticker"]

            database[ticker] = {
                "company": company,
                "ticker": ticker,
                "category": category,
                "description": information["description"],
            }

    return database


STOCK_DATABASE = build_stock_database()


# =========================================================
# Yahoo Finance 데이터 조회
# =========================================================
@st.cache_data(ttl=1800, show_spinner=False)
def download_stock_data(ticker, period, interval="1d"):
    """
    Yahoo Finance에서 주가 데이터를 조회합니다.

    1차로 yf.download()를 사용하고,
    실패하면 Ticker.history()로 재시도합니다.
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

    # yfinance가 단일 종목에도 MultiIndex 열을 반환하는 경우 처리
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

    # 시간대 정보 제거
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
        ticker = item["ticker"]
        company = item["company"]

        progress_text.caption(
            f"일봉 데이터 조회 중: {company} ({ticker})"
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

        progress_bar.progress(
            (index + 1) / total_count
        )

        # 연속 요청 속도를 조금 늦춤
        time.sleep(0.05)

    progress_bar.empty()
    progress_text.empty()

    return loaded_data, failed_tickers


# =========================================================
# 기술적 지표
# =========================================================
def add_technical_indicators(data):
    result = data.copy()

    price = result["Adj Close"]

    # 이동평균
    result["MA5"] = price.rolling(5).mean()
    result["MA20"] = price.rolling(20).mean()
    result["MA60"] = price.rolling(60).mean()
    result["MA120"] = price.rolling(120).mean()

    # 거래량 이동평균
    result["Volume_MA20"] = (
        result["Volume"]
        .rolling(20)
        .mean()
    )

    # 볼린저밴드
    result["BB_Middle"] = price.rolling(20).mean()

    rolling_std = price.rolling(20).std()

    result["BB_Upper"] = (
        result["BB_Middle"]
        + 2 * rolling_std
    )

    result["BB_Lower"] = (
        result["BB_Middle"]
        - 2 * rolling_std
    )

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

    relative_strength = (
        average_gain
        / average_loss.replace(0, pd.NA)
    )

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

    result["MACD_Signal"] = (
        result["MACD"]
        .ewm(
            span=9,
            adjust=False,
        )
        .mean()
    )

    result["MACD_Histogram"] = (
        result["MACD"]
        - result["MACD_Signal"]
    )

    # 일간 수익률
    result["Daily_Return"] = (
        price.pct_change()
    )

    return result


# =========================================================
# 성과 지표
# =========================================================
def calculate_period_return(price, trading_days):
    if price.empty or len(price) <= trading_days:
        return None

    previous_price = price.iloc[
        -trading_days - 1
    ]

    if previous_price == 0:
        return None

    return (
        price.iloc[-1]
        / previous_price
        - 1
    ) * 100


def calculate_max_drawdown(price):
    if price.empty:
        return None

    peak = price.cummax()
    drawdown = price / peak - 1

    return drawdown.min() * 100


def calculate_metrics(data):
    price = data["Adj Close"].dropna()

    if price.empty:
        return {}

    current_price = price.iloc[-1]

    previous_price = (
        price.iloc[-2]
        if len(price) >= 2
        else current_price
    )

    daily_return = (
        (current_price / previous_price - 1) * 100
        if previous_price != 0
        else None
    )

    first_price = price.iloc[0]

    total_return = (
        (current_price / first_price - 1) * 100
        if first_price != 0
        else None
    )

    daily_returns = (
        price.pct_change().dropna()
    )

    volatility = (
        daily_returns.std()
        * (252 ** 0.5)
        * 100
        if not daily_returns.empty
        else None
    )

    latest_volume = data["Volume"].iloc[-1]

    average_volume_20 = (
        data["Volume"]
        .rolling(20)
        .mean()
        .iloc[-1]
    )

    volume_ratio = None

    if (
        pd.notna(average_volume_20)
        and average_volume_20 != 0
    ):
        volume_ratio = (
            latest_volume
            / average_volume_20
        )

    return {
        "current_price": current_price,
        "daily_return": daily_return,
        "total_return": total_return,
        "return_1w": calculate_period_return(
            price,
            5,
        ),
        "return_1m": calculate_period_return(
            price,
            21,
        ),
        "return_3m": calculate_period_return(
            price,
            63,
        ),
        "return_6m": calculate_period_return(
            price,
            126,
        ),
        "volatility": volatility,
        "max_drawdown": calculate_max_drawdown(
            price
        ),
        "period_high": price.max(),
        "period_low": price.min(),
        "latest_volume": latest_volume,
        "volume_ratio": volume_ratio,
    }


def calculate_trend_score(metrics, data):
    """
    수익률, 추세 및 거래량을 조합한 상대 점수입니다.
    투자 추천 점수가 아닙니다.
    """

    score = 50.0

    return_1w = metrics.get("return_1w")
    return_1m = metrics.get("return_1m")
    return_3m = metrics.get("return_3m")
    volatility = metrics.get("volatility")
    volume_ratio = metrics.get("volume_ratio")

    if return_1w is not None:
        score += max(
            -8,
            min(8, return_1w * 0.7),
        )

    if return_1m is not None:
        score += max(
            -10,
            min(10, return_1m * 0.4),
        )

    if return_3m is not None:
        score += max(
            -10,
            min(10, return_3m * 0.2),
        )

    latest = data.iloc[-1]

    current_price = latest.get("Adj Close")
    ma20 = latest.get("MA20")
    ma60 = latest.get("MA60")
    rsi = latest.get("RSI")
    macd = latest.get("MACD")
    macd_signal = latest.get("MACD_Signal")

    if pd.notna(current_price) and pd.notna(ma20):
        score += (
            5
            if current_price > ma20
            else -5
        )

    if pd.notna(current_price) and pd.notna(ma60):
        score += (
            5
            if current_price > ma60
            else -5
        )

    if pd.notna(rsi):
        if 45 <= rsi <= 65:
            score += 3
        elif rsi >= 75:
            score -= 3
        elif rsi <= 30:
            score -= 2

    if (
        pd.notna(macd)
        and pd.notna(macd_signal)
    ):
        score += (
            4
            if macd > macd_signal
            else -4
        )

    if volume_ratio is not None:
        if (
            volume_ratio >= 1.5
            and metrics.get("daily_return", 0) > 0
        ):
            score += 4
        elif (
            volume_ratio >= 1.5
            and metrics.get("daily_return", 0) < 0
        ):
            score -= 3

    if volatility is not None:
        if volatility > 70:
            score -= 4
        elif volatility < 35:
            score += 2

    return round(
        max(0, min(100, score)),
        1,
    )


def get_score_label(score):
    if score >= 75:
        return "강한 상승 추세"
    if score >= 60:
        return "상승 우위"
    if score >= 45:
        return "중립"
    if score >= 30:
        return "약세"
    return "강한 약세"


# =========================================================
# 표시 함수
# =========================================================
def format_number(value, digits=0):
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

    return f"{value:.2f}배"


def dataframe_to_csv(dataframe):
    return dataframe.to_csv(
        index=True
    ).encode("utf-8-sig")


# =========================================================
# 차트 생성 함수
# =========================================================
def create_daily_candlestick_chart(
    data,
    company,
):
    """
    일봉 캔들스틱과 이동평균선을 표시합니다.
    """

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="일봉",
            increasing_line_color="#ef5350",
            decreasing_line_color="#2962ff",
            increasing_fillcolor="#ef5350",
            decreasing_fillcolor="#2962ff",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA5"],
            mode="lines",
            name="5일선",
            line=dict(width=1.2),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA20"],
            mode="lines",
            name="20일선",
            line=dict(width=1.5),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA60"],
            mode="lines",
            name="60일선",
            line=dict(width=1.5),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA120"],
            mode="lines",
            name="120일선",
            line=dict(width=1.4),
        )
    )

    fig.update_layout(
        title=f"{company} 일봉 차트",
        xaxis_title="날짜",
        yaxis_title="주가(원)",
        height=650,
        xaxis_rangeslider_visible=True,
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    fig.update_xaxes(
        rangebreaks=[
            dict(
                bounds=["sat", "mon"]
            ),
        ]
    )

    return fig


def create_price_volume_chart(
    data,
    company,
):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Adj Close"],
            mode="lines",
            name="수정주가",
            line=dict(width=2.5),
            yaxis="y1",
        )
    )

    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data["Volume"],
            name="거래량",
            opacity=0.35,
            yaxis="y2",
        )
    )

    fig.update_layout(
        title=f"{company} 주가와 거래량",
        xaxis=dict(
            title="날짜",
            rangebreaks=[
                dict(
                    bounds=["sat", "mon"]
                )
            ],
        ),
        yaxis=dict(
            title="주가(원)",
            side="left",
        ),
        yaxis2=dict(
            title="거래량",
            side="right",
            overlaying="y",
            showgrid=False,
        ),
        height=550,
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        legend=dict(
            orientation="h",
            y=1.02,
            x=1,
            xanchor="right",
        ),
    )

    return fig


def create_bollinger_chart(
    data,
    company,
):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["BB_Upper"],
            mode="lines",
            name="상단 밴드",
            line=dict(width=1),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["BB_Lower"],
            mode="lines",
            name="하단 밴드",
            line=dict(width=1),
            fill="tonexty",
            fillcolor="rgba(128,128,128,0.12)",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["BB_Middle"],
            mode="lines",
            name="20일 중심선",
            line=dict(width=1.3),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Adj Close"],
            mode="lines",
            name="주가",
            line=dict(width=2.5),
        )
    )

    fig.update_layout(
        title=f"{company} 볼린저밴드",
        xaxis_title="날짜",
        yaxis_title="주가(원)",
        height=520,
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
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
        annotation_text="과열 70",
    )

    fig.add_hline(
        y=30,
        line_dash="dash",
        annotation_text="과매도 30",
    )

    fig.update_layout(
        title=f"{company} RSI",
        xaxis_title="날짜",
        yaxis_title="RSI",
        yaxis_range=[0, 100],
        height=390,
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
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
        height=420,
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
    )

    return fig


def create_relative_return_chart(
    comparison_data,
):
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
        title="관련 종목 상대수익률 비교",
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
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        legend=dict(
            orientation="h",
            y=1.02,
            x=1,
            xanchor="right",
            yanchor="bottom",
        ),
    )

    return fig


def create_return_ranking_chart(
    summary_data,
    period_label,
):
    chart_data = (
        summary_data
        .sort_values(
            by="기간 수익률(%)",
            ascending=True,
        )
        .copy()
    )

    fig = px.bar(
        chart_data,
        x="기간 수익률(%)",
        y="종목",
        orientation="h",
        color="분류",
        title=f"{period_label} 수익률 순위",
        text="기간 수익률(%)",
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
        hovertemplate=(
            "종목: %{y}<br>"
            "수익률: %{x:.2f}%"
            "<extra></extra>"
        ),
    )

    fig.add_vline(
        x=0,
        line_dash="dash",
    )

    fig.update_layout(
        height=max(
            450,
            len(chart_data) * 52,
        ),
        margin=dict(
            l=20,
            r=50,
            t=60,
            b=20,
        ),
        showlegend=True,
    )

    return fig


def create_risk_return_chart(
    summary_data,
):
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
        color="분류",
        size="추세 점수",
        hover_name="종목",
        hover_data={
            "티커": True,
            "1개월 수익률(%)": ":.2f",
            "거래량 배율": ":.2f",
            "추세 점수": ":.1f",
        },
        title="위험·수익률 비교",
        size_max=45,
    )

    fig.add_hline(
        y=0,
        line_dash="dash",
    )

    fig.update_layout(
        height=580,
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
    )

    return fig


# =========================================================
# 화면 헤더
# =========================================================
st.title("⚡ 두산에너빌리티 및 관련주 동향")

st.caption(
    "두산에너빌리티를 중심으로 원전 설계·정비, "
    "계측·제어, 발전설비 및 전력 인프라 관련 종목의 "
    "일봉과 상대 동향을 비교합니다."
)

st.warning(
    "관련주 분류와 추세 점수는 가격 흐름을 비교하기 위한 "
    "참고 자료입니다. 사업의 직접적 경쟁관계나 매수·매도 추천을 "
    "의미하지 않습니다."
)


# =========================================================
# 사이드바
# =========================================================
with st.sidebar:
    st.header("분석 설정")

    category_options = list(
        RELATED_STOCKS.keys()
    )

    selected_categories = st.multiselect(
        "관련 분야",
        options=category_options,
        default=category_options,
    )

    available_items = [
        item
        for item in STOCK_DATABASE.values()
        if item["category"]
        in selected_categories
    ]

    label_to_ticker = {
        (
            f"{item['company']} "
            f"({item['ticker']})"
        ): item["ticker"]
        for item in available_items
    }

    default_companies = [
        "두산에너빌리티",
        "한전기술",
        "한전KPS",
        "비에이치아이",
        "우진",
        "우리기술",
        "HD현대일렉트릭",
        "LS ELECTRIC",
    ]

    default_labels = [
        label
        for label in label_to_ticker
        if any(
            company in label
            for company in default_companies
        )
    ]

    selected_labels = st.multiselect(
        "비교 종목",
        options=list(label_to_ticker.keys()),
        default=default_labels,
        help=(
            "Yahoo Finance 요청 제한을 고려해 "
            "5~10개 종목을 권장합니다."
        ),
    )

    period_label = st.selectbox(
        "분석 기간",
        options=list(
            PERIOD_OPTIONS.keys()
        ),
        index=4,
    )

    benchmark_name = st.selectbox(
        "비교 지수",
        options=list(
            BENCHMARKS.keys()
        ),
        index=0,
    )

    include_benchmark = st.checkbox(
        "상대수익률에 비교 지수 포함",
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
        "일봉 데이터는 30분 동안 캐시됩니다."
    )


# =========================================================
# 선택값 확인
# =========================================================
if not selected_categories:
    st.info(
        "하나 이상의 관련 분야를 선택해 주세요."
    )
    st.stop()

if not selected_labels:
    st.info(
        "하나 이상의 종목을 선택해 주세요."
    )
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
# 데이터 로딩
# =========================================================
with st.spinner(
    "두산에너빌리티 관련 종목의 일봉 데이터를 불러오는 중입니다..."
):
    loaded_data, failed_tickers = (
        load_multiple_stocks(
            selected_stock_items,
            period,
        )
    )


if failed_tickers:
    st.warning(
        "다음 티커의 데이터를 불러오지 못했습니다: "
        + ", ".join(failed_tickers)
        + "\n\n종목 수를 줄이거나 잠시 후 다시 접속해 보세요."
    )


if not loaded_data:
    st.error(
        "조회 가능한 데이터가 없습니다. "
        "Yahoo Finance의 일시적인 접속 제한일 수 있습니다."
    )
    st.stop()


# =========================================================
# 분석 데이터 생성
# =========================================================
technical_data_map = {}
summary_rows = []

for ticker, loaded_item in loaded_data.items():
    information = loaded_item["information"]

    technical_data = (
        add_technical_indicators(
            loaded_item["data"]
        )
    )

    technical_data_map[ticker] = (
        technical_data
    )

    metrics = calculate_metrics(
        technical_data
    )

    trend_score = calculate_trend_score(
        metrics,
        technical_data,
    )

    latest = technical_data.iloc[-1]

    latest_rsi = latest.get("RSI")
    latest_macd = latest.get("MACD")
    latest_signal = latest.get(
        "MACD_Signal"
    )

    macd_status = "-"

    if (
        pd.notna(latest_macd)
        and pd.notna(latest_signal)
    ):
        macd_status = (
            "상승"
            if latest_macd > latest_signal
            else "하락"
        )

    summary_rows.append(
        {
            "종목": information["company"],
            "티커": ticker,
            "분류": information["category"],
            "현재가": metrics.get(
                "current_price"
            ),
            "일간 등락률(%)": metrics.get(
                "daily_return"
            ),
            "1주 수익률(%)": metrics.get(
                "return_1w"
            ),
            "1개월 수익률(%)": metrics.get(
                "return_1m"
            ),
            "3개월 수익률(%)": metrics.get(
                "return_3m"
            ),
            "6개월 수익률(%)": metrics.get(
                "return_6m"
            ),
            "기간 수익률(%)": metrics.get(
                "total_return"
            ),
            "연환산 변동성(%)": metrics.get(
                "volatility"
            ),
            "최대 낙폭(%)": metrics.get(
                "max_drawdown"
            ),
            "거래량 배율": metrics.get(
                "volume_ratio"
            ),
            "RSI": latest_rsi,
            "MACD 상태": macd_status,
            "추세 점수": trend_score,
            "추세 해석": get_score_label(
                trend_score
            ),
        }
    )


summary_data = pd.DataFrame(
    summary_rows
)

summary_data = summary_data.sort_values(
    by="추세 점수",
    ascending=False,
).reset_index(drop=True)

summary_data.index = (
    summary_data.index + 1
)

summary_data.index.name = "순위"


# =========================================================
# 두산에너빌리티 핵심 요약
# =========================================================
st.header("🏭 두산에너빌리티 핵심 현황")

doosan_ticker = "034020.KS"

if doosan_ticker in technical_data_map:
    doosan_data = technical_data_map[
        doosan_ticker
    ]

    doosan_metrics = calculate_metrics(
        doosan_data
    )

    doosan_score = calculate_trend_score(
        doosan_metrics,
        doosan_data,
    )

    doosan_latest = doosan_data.iloc[-1]

    metric_columns = st.columns(6)

    with metric_columns[0]:
        st.metric(
            "현재가",
            (
                f"₩"
                f"{format_number(doosan_metrics['current_price'])}"
            ),
            format_percent(
                doosan_metrics["daily_return"]
            ),
        )

    with metric_columns[1]:
        st.metric(
            "1주 수익률",
            format_percent(
                doosan_metrics["return_1w"]
            ),
        )

    with metric_columns[2]:
        st.metric(
            "1개월 수익률",
            format_percent(
                doosan_metrics["return_1m"]
            ),
        )

    with metric_columns[3]:
        st.metric(
            f"{period_label} 수익률",
            format_percent(
                doosan_metrics["total_return"]
            ),
        )

    with metric_columns[4]:
        st.metric(
            "거래량 배율",
            format_ratio(
                doosan_metrics["volume_ratio"]
            ),
            help=(
                "최근 거래량을 20일 평균 거래량으로 "
                "나눈 값입니다."
            ),
        )

    with metric_columns[5]:
        st.metric(
            "추세 점수",
            f"{doosan_score:.1f}점",
            get_score_label(
                doosan_score
            ),
        )

    st.plotly_chart(
        create_daily_candlestick_chart(
            doosan_data,
            "두산에너빌리티",
        ),
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": True,
        },
    )

    latest_messages = []

    current_price = doosan_latest.get(
        "Adj Close"
    )

    ma20 = doosan_latest.get("MA20")
    ma60 = doosan_latest.get("MA60")
    rsi = doosan_latest.get("RSI")
    macd = doosan_latest.get("MACD")
    macd_signal = doosan_latest.get(
        "MACD_Signal"
    )

    if pd.notna(ma20):
        latest_messages.append(
            (
                "현재 주가는 20일 이동평균선 위에 있습니다."
                if current_price > ma20
                else "현재 주가는 20일 이동평균선 아래에 있습니다."
            )
        )

    if pd.notna(ma60):
        latest_messages.append(
            (
                "60일선 기준 중기 추세는 상승 우위입니다."
                if current_price > ma60
                else "60일선 기준 중기 추세는 약세 우위입니다."
            )
        )

    if pd.notna(rsi):
        if rsi >= 70:
            latest_messages.append(
                f"RSI는 {rsi:.1f}로 단기 과열 범위입니다."
            )
        elif rsi <= 30:
            latest_messages.append(
                f"RSI는 {rsi:.1f}로 단기 과매도 범위입니다."
            )
        else:
            latest_messages.append(
                f"RSI는 {rsi:.1f}로 중립 범위입니다."
            )

    if (
        pd.notna(macd)
        and pd.notna(macd_signal)
    ):
        latest_messages.append(
            (
                "MACD가 시그널선을 상회합니다."
                if macd > macd_signal
                else "MACD가 시그널선을 하회합니다."
            )
        )

    if latest_messages:
        st.info(
            " ".join(latest_messages)
        )

else:
    st.info(
        "비교 종목에 두산에너빌리티를 포함하면 "
        "두산에너빌리티 핵심 현황이 표시됩니다."
    )


# =========================================================
# 관련주 시장 요약
# =========================================================
st.divider()
st.header("📊 관련주 시장 요약")

positive_stocks = (
    summary_data["일간 등락률(%)"] > 0
).sum()

median_daily_return = (
    summary_data["일간 등락률(%)"]
    .median()
)

median_period_return = (
    summary_data["기간 수익률(%)"]
    .median()
)

top_stock = summary_data.iloc[0]

market_columns = st.columns(4)

with market_columns[0]:
    st.metric(
        "상승 종목 수",
        (
            f"{positive_stocks}"
            f" / {len(summary_data)}"
        ),
    )

with market_columns[1]:
    st.metric(
        "일간 등락률 중앙값",
        format_percent(
            median_daily_return
        ),
    )

with market_columns[2]:
    st.metric(
        f"{period_label} 수익률 중앙값",
        format_percent(
            median_period_return
        ),
    )

with market_columns[3]:
    st.metric(
        "최고 추세 종목",
        top_stock["종목"],
        f"{top_stock['추세 점수']:.1f}점",
    )


# =========================================================
# 비교 탭
# =========================================================
(
    ranking_tab,
    relative_tab,
    risk_tab,
) = st.tabs(
    [
        "종목 순위",
        "상대수익률",
        "위험·수익률",
    ]
)

with ranking_tab:
    ranking_columns = [
        "종목",
        "티커",
        "분류",
        "현재가",
        "일간 등락률(%)",
        "1주 수익률(%)",
        "1개월 수익률(%)",
        "3개월 수익률(%)",
        "기간 수익률(%)",
        "거래량 배율",
        "RSI",
        "MACD 상태",
        "추세 점수",
        "추세 해석",
    ]

    ranking_display = summary_data[
        ranking_columns
    ].copy()

    round_columns = [
        "현재가",
        "일간 등락률(%)",
        "1주 수익률(%)",
        "1개월 수익률(%)",
        "3개월 수익률(%)",
        "기간 수익률(%)",
        "거래량 배율",
        "RSI",
        "추세 점수",
    ]

    for column in round_columns:
        ranking_display[column] = (
            ranking_display[column]
            .round(2)
        )

    st.dataframe(
        ranking_display,
        use_container_width=True,
        height=min(
            650,
            60
            + len(ranking_display) * 38,
        ),
        column_config={
            "현재가": st.column_config.NumberColumn(
                format="%,.0f원",
            ),
            "일간 등락률(%)": st.column_config.NumberColumn(
                format="%.2f%%",
            ),
            "1주 수익률(%)": st.column_config.NumberColumn(
                format="%.2f%%",
            ),
            "1개월 수익률(%)": st.column_config.NumberColumn(
                format="%.2f%%",
            ),
            "3개월 수익률(%)": st.column_config.NumberColumn(
                format="%.2f%%",
            ),
            "기간 수익률(%)": st.column_config.NumberColumn(
                format="%.2f%%",
            ),
            "거래량 배율": st.column_config.NumberColumn(
                format="%.2f배",
            ),
            "추세 점수": st.column_config.ProgressColumn(
                min_value=0,
                max_value=100,
                format="%.1f",
            ),
        },
    )

    st.plotly_chart(
        create_return_ranking_chart(
            summary_data.reset_index(),
            period_label,
        ),
        use_container_width=True,
        config={
            "displaylogo": False,
        },
    )

    st.download_button(
        label="관련주 분석 결과 CSV 다운로드",
        data=dataframe_to_csv(
            ranking_display
        ),
        file_name=(
            "doosan_related_stocks_"
            f"{datetime.now().strftime('%Y%m%d')}.csv"
        ),
        mime="text/csv",
    )

with relative_tab:
    normalized_series = {}

    for ticker, data in (
        technical_data_map.items()
    ):
        price = (
            data["Adj Close"]
            .dropna()
        )

        if (
            price.empty
            or price.iloc[0] == 0
        ):
            continue

        company = STOCK_DATABASE[
            ticker
        ]["company"]

        normalized_series[
            f"{company} ({ticker})"
        ] = (
            price
            / price.iloc[0]
            * 100
        )

    if include_benchmark:
        benchmark_ticker = (
            BENCHMARKS[benchmark_name]
        )

        benchmark_data = (
            download_stock_data(
                benchmark_ticker,
                period,
                "1d",
            )
        )

        if not benchmark_data.empty:
            benchmark_price = (
                benchmark_data[
                    "Adj Close"
                ]
                .dropna()
            )

            if (
                not benchmark_price.empty
                and benchmark_price.iloc[0] != 0
            ):
                normalized_series[
                    benchmark_name
                ] = (
                    benchmark_price
                    / benchmark_price.iloc[0]
                    * 100
                )
        else:
            st.info(
                "비교 지수 데이터를 불러오지 못했습니다."
            )

    if normalized_series:
        comparison_data = pd.concat(
            normalized_series,
            axis=1,
        ).sort_index()

        comparison_data.index.name = "Date"

        st.plotly_chart(
            create_relative_return_chart(
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
        "오른쪽으로 갈수록 변동성이 크고, "
        "위쪽으로 갈수록 선택 기간 수익률이 높습니다."
    )


# =========================================================
# 개별 종목 일봉 분석
# =========================================================
st.divider()
st.header("🔍 개별 종목 일봉 분석")

detail_options = {
    (
        f"{STOCK_DATABASE[ticker]['company']} "
        f"({ticker})"
    ): ticker
    for ticker in technical_data_map
}

default_detail_index = 0

detail_labels = list(
    detail_options.keys()
)

for index, label in enumerate(
    detail_labels
):
    if "두산에너빌리티" in label:
        default_detail_index = index
        break


selected_detail_label = st.selectbox(
    "상세 분석 종목",
    options=detail_labels,
    index=default_detail_index,
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

detail_metrics = calculate_metrics(
    detail_data
)

detail_score = calculate_trend_score(
    detail_metrics,
    detail_data,
)


st.subheader(
    f"{detail_information['company']} · "
    f"{detail_ticker}"
)

st.caption(
    f"{detail_information['category']} | "
    f"{detail_information['description']}"
)


detail_columns = st.columns(6)

with detail_columns[0]:
    st.metric(
        "현재가",
        (
            f"₩"
            f"{format_number(detail_metrics['current_price'])}"
        ),
        format_percent(
            detail_metrics["daily_return"]
        ),
    )

with detail_columns[1]:
    st.metric(
        "1주 수익률",
        format_percent(
            detail_metrics["return_1w"]
        ),
    )

with detail_columns[2]:
    st.metric(
        "1개월 수익률",
        format_percent(
            detail_metrics["return_1m"]
        ),
    )

with detail_columns[3]:
    st.metric(
        "거래량 배율",
        format_ratio(
            detail_metrics["volume_ratio"]
        ),
    )

with detail_columns[4]:
    st.metric(
        "최대 낙폭",
        format_percent(
            detail_metrics["max_drawdown"]
        ),
    )

with detail_columns[5]:
    st.metric(
        "추세 점수",
        f"{detail_score:.1f}점",
        get_score_label(
            detail_score
        ),
    )


(
    daily_tab,
    volume_tab,
    band_tab,
    momentum_tab,
    raw_tab,
) = st.tabs(
    [
        "일봉",
        "주가·거래량",
        "볼린저밴드",
        "RSI·MACD",
        "원본 데이터",
    ]
)

with daily_tab:
    st.plotly_chart(
        create_daily_candlestick_chart(
            detail_data,
            detail_information["company"],
        ),
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": True,
        },
    )

with volume_tab:
    st.plotly_chart(
        create_price_volume_chart(
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

with raw_tab:
    raw_display = detail_data[
        [
            "Open",
            "High",
            "Low",
            "Close",
            "Adj Close",
            "Volume",
            "MA5",
            "MA20",
            "MA60",
            "MA120",
            "RSI",
            "MACD",
            "MACD_Signal",
        ]
    ].copy()

    raw_display.index = (
        raw_display.index.strftime(
            "%Y-%m-%d"
        )
    )

    raw_display.index.name = "Date"

    st.dataframe(
        raw_display.sort_index(
            ascending=False
        ),
        use_container_width=True,
    )

    st.download_button(
        label=(
            f"{detail_ticker} "
            "일봉 데이터 CSV 다운로드"
        ),
        data=dataframe_to_csv(
            raw_display
        ),
        file_name=(
            f"{detail_ticker}_daily_"
            f"{datetime.now().strftime('%Y%m%d')}.csv"
        ),
        mime="text/csv",
    )


# =========================================================
# 점수 설명 및 면책
# =========================================================
st.divider()

with st.expander("추세 점수 산정 방식"):
    st.markdown(
        """
        추세 점수는 다음 가격 지표를 조합한 0~100점의
        상대 비교 지표입니다.

        - 최근 1주, 1개월 및 3개월 수익률
        - 현재 주가의 20일·60일 이동평균선 상회 여부
        - RSI 수준
        - MACD와 시그널선의 관계
        - 최근 거래량과 20일 평균 거래량의 비율
        - 연환산 변동성

        거래량이 증가하면서 주가가 상승한 경우에는 점수가
        일부 높아지고, 거래량이 증가하면서 주가가 하락한
        경우에는 점수가 일부 낮아집니다.

        이 점수에는 수주, 매출, 영업이익, 기업가치,
        정책 변화 및 원전 프로젝트 진행 상황이 반영되지 않습니다.
        """
    )


st.info(
    "Yahoo Finance의 한국 주식 데이터는 지연되거나 "
    "일시적으로 조회되지 않을 수 있습니다. "
    "본 대시보드는 정보 제공용이며 투자 권유를 목적으로 하지 않습니다."
)
