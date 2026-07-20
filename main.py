from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf


# ---------------------------------------------------------
# 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="글로벌 주요 주식 대시보드",
    page_icon="📈",
    layout="wide",
)


# ---------------------------------------------------------
# 기본 종목 목록
# Yahoo Finance에서 사용하는 티커 기준
# ---------------------------------------------------------
STOCK_GROUPS = {
    "미국": {
        "Apple": "AAPL",
        "Microsoft": "MSFT",
        "NVIDIA": "NVDA",
        "Amazon": "AMZN",
        "Alphabet": "GOOGL",
        "Meta": "META",
        "Tesla": "TSLA",
        "JPMorgan Chase": "JPM",
        "Berkshire Hathaway": "BRK-B",
        "Eli Lilly": "LLY",
    },
    "한국": {
        "삼성전자": "005930.KS",
        "SK하이닉스": "000660.KS",
        "현대차": "005380.KS",
        "기아": "000270.KS",
        "NAVER": "035420.KS",
        "카카오": "035720.KS",
        "LG에너지솔루션": "373220.KS",
        "삼성바이오로직스": "207940.KS",
        "셀트리온": "068270.KS",
        "KB금융": "105560.KS",
    },
    "일본": {
        "Toyota": "7203.T",
        "Sony": "6758.T",
        "Mitsubishi UFJ": "8306.T",
        "Nintendo": "7974.T",
        "SoftBank Group": "9984.T",
        "Hitachi": "6501.T",
        "Keyence": "6861.T",
        "Recruit Holdings": "6098.T",
    },
    "유럽": {
        "ASML": "ASML.AS",
        "SAP": "SAP.DE",
        "Novo Nordisk": "NOVO-B.CO",
        "LVMH": "MC.PA",
        "Siemens": "SIE.DE",
        "Airbus": "AIR.PA",
        "Shell": "SHEL.L",
        "Unilever": "ULVR.L",
    },
    "중국·홍콩": {
        "Tencent": "0700.HK",
        "Alibaba": "9988.HK",
        "BYD": "1211.HK",
        "Xiaomi": "1810.HK",
        "Meituan": "3690.HK",
        "JD.com": "9618.HK",
        "China Mobile": "0941.HK",
        "Ping An Insurance": "2318.HK",
    },
    "글로벌 지수": {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "Dow Jones": "^DJI",
        "KOSPI": "^KS11",
        "Nikkei 225": "^N225",
        "Hang Seng": "^HSI",
        "DAX": "^GDAXI",
        "FTSE 100": "^FTSE",
    },
}


PERIOD_OPTIONS = {
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "연초 이후": "ytd",
    "1년": "1y",
    "2년": "2y",
    "5년": "5y",
    "10년": "10y",
    "전체": "max",
}


INTERVAL_OPTIONS = {
    "일봉": "1d",
    "주봉": "1wk",
    "월봉": "1mo",
}


# ---------------------------------------------------------
# 보조 함수
# ---------------------------------------------------------
def format_number(value, decimal_places=2):
    """숫자를 화면 표시용 문자열로 변환합니다."""
    if value is None or pd.isna(value):
        return "-"

    return f"{value:,.{decimal_places}f}"


def format_percentage(value):
    """수익률 등의 값을 백분율 문자열로 변환합니다."""
    if value is None or pd.isna(value):
        return "-"

    return f"{value:+.2f}%"


def get_currency_symbol(currency):
    """통화 코드에 따라 간단한 통화 기호를 반환합니다."""
    symbols = {
        "USD": "$",
        "KRW": "₩",
        "JPY": "¥",
        "EUR": "€",
        "GBP": "£",
        "HKD": "HK$",
        "CNY": "¥",
        "CHF": "CHF ",
        "DKK": "DKK ",
    }

    return symbols.get(currency, f"{currency} " if currency else "")


@st.cache_data(ttl=900, show_spinner=False)
def load_stock_data(ticker, period, interval):
    """
    Yahoo Finance에서 개별 종목의 가격 데이터를 조회합니다.

    auto_adjust=False로 설정하여 원시 OHLC와 Adj Close를 함께 사용합니다.
    """
    data = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    if data is None or data.empty:
        return pd.DataFrame()

    # 일부 yfinance 버전에서는 단일 티커도 MultiIndex 열을 반환할 수 있습니다.
    if isinstance(data.columns, pd.MultiIndex):
        first_level = data.columns.get_level_values(0)

        if "Close" in first_level:
            data.columns = first_level
        else:
            data.columns = data.columns.get_level_values(-1)

    data = data.copy()
    data.index = pd.to_datetime(data.index)

    # 시간대 정보가 있는 경우 제거하여 Plotly 및 CSV 처리를 단순화합니다.
    if getattr(data.index, "tz", None) is not None:
        data.index = data.index.tz_localize(None)

    required_columns = ["Open", "High", "Low", "Close", "Volume"]

    for column in required_columns:
        if column not in data.columns:
            data[column] = pd.NA

    # Adj Close가 없는 경우 Close를 대신 사용합니다.
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
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna(subset=["Close"])

    return data


@st.cache_data(ttl=3600, show_spinner=False)
def load_ticker_metadata(ticker):
    """
    종목명과 통화 정보를 조회합니다.

    Yahoo Finance에서 메타데이터 조회가 실패하면 티커를 종목명으로 사용합니다.
    """
    default_result = {
        "name": ticker,
        "currency": "",
        "exchange": "",
        "sector": "",
        "industry": "",
    }

    try:
        stock = yf.Ticker(ticker)
        info = stock.get_info()

        if not isinstance(info, dict):
            return default_result

        return {
            "name": (
                info.get("longName")
                or info.get("shortName")
                or info.get("displayName")
                or ticker
            ),
            "currency": info.get("currency") or "",
            "exchange": (
                info.get("fullExchangeName")
                or info.get("exchange")
                or ""
            ),
            "sector": info.get("sector") or "",
            "industry": info.get("industry") or "",
        }

    except Exception:
        return default_result


def calculate_metrics(data):
    """가격 데이터에서 주요 지표를 계산합니다."""
    close = data["Adj Close"].dropna()

    if close.empty:
        return {
            "current_price": None,
            "previous_price": None,
            "daily_change": None,
            "period_return": None,
            "period_high": None,
            "period_low": None,
            "annual_volatility": None,
        }

    current_price = close.iloc[-1]
    previous_price = close.iloc[-2] if len(close) >= 2 else close.iloc[-1]

    daily_change = (
        (current_price / previous_price - 1) * 100
        if previous_price != 0
        else None
    )

    first_price = close.iloc[0]

    period_return = (
        (current_price / first_price - 1) * 100
        if first_price != 0
        else None
    )

    daily_returns = close.pct_change().dropna()

    annual_volatility = (
        daily_returns.std() * (252 ** 0.5) * 100
        if not daily_returns.empty
        else None
    )

    return {
        "current_price": current_price,
        "previous_price": previous_price,
        "daily_change": daily_change,
        "period_return": period_return,
        "period_high": close.max(),
        "period_low": close.min(),
        "annual_volatility": annual_volatility,
    }


def create_price_chart(data, ticker_name, show_ma20, show_ma60):
    """수정주가와 이동평균선을 표시하는 Plotly 차트를 생성합니다."""
    chart_data = data.copy()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=chart_data.index,
            y=chart_data["Adj Close"],
            mode="lines",
            name="수정주가",
            hovertemplate=(
                "%{x|%Y-%m-%d}<br>"
                "수정주가: %{y:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    if show_ma20:
        chart_data["MA20"] = chart_data["Adj Close"].rolling(20).mean()

        fig.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data["MA20"],
                mode="lines",
                name="20일 이동평균",
                hovertemplate=(
                    "%{x|%Y-%m-%d}<br>"
                    "20일 이동평균: %{y:,.2f}"
                    "<extra></extra>"
                ),
            )
        )

    if show_ma60:
        chart_data["MA60"] = chart_data["Adj Close"].rolling(60).mean()

        fig.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data["MA60"],
                mode="lines",
                name="60일 이동평균",
                hovertemplate=(
                    "%{x|%Y-%m-%d}<br>"
                    "60일 이동평균: %{y:,.2f}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=f"{ticker_name} 주가 추이",
        xaxis_title="날짜",
        yaxis_title="가격",
        hovermode="x unified",
        height=520,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    fig.update_xaxes(
        rangeslider_visible=True,
        rangebreaks=[
            dict(bounds=["sat", "mon"]),
        ],
    )

    return fig


def create_candlestick_chart(data, ticker_name):
    """OHLC 데이터를 이용한 캔들스틱 차트를 생성합니다."""
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name=ticker_name,
            increasing_line_color="#ef5350",
            decreasing_line_color="#2962ff",
            hovertext=data.index.strftime("%Y-%m-%d"),
        )
    )

    fig.update_layout(
        title=f"{ticker_name} 캔들스틱 차트",
        xaxis_title="날짜",
        yaxis_title="가격",
        height=570,
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis_rangeslider_visible=False,
    )

    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),
        ]
    )

    return fig


def create_volume_chart(data, ticker_name):
    """거래량 막대 차트를 생성합니다."""
    volume_data = data.reset_index()

    date_column = volume_data.columns[0]

    fig = px.bar(
        volume_data,
        x=date_column,
        y="Volume",
        title=f"{ticker_name} 거래량",
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
        height=380,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False,
    )

    return fig


def create_comparison_chart(comparison_data):
    """여러 종목의 시작점을 100으로 맞춘 비교 차트를 생성합니다."""
    long_data = (
        comparison_data
        .reset_index()
        .melt(
            id_vars=comparison_data.index.name or "Date",
            var_name="종목",
            value_name="정규화 지수",
        )
    )

    date_column = long_data.columns[0]

    fig = px.line(
        long_data,
        x=date_column,
        y="정규화 지수",
        color="종목",
        title="종목별 정규화 수익률 비교",
        labels={
            date_column: "날짜",
            "정규화 지수": "시작일 = 100",
        },
    )

    fig.update_traces(
        hovertemplate=(
            "%{x|%Y-%m-%d}<br>"
            "정규화 지수: %{y:,.2f}"
            "<extra></extra>"
        )
    )

    fig.add_hline(
        y=100,
        line_dash="dash",
        annotation_text="시작점",
    )

    fig.update_layout(
        height=570,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    return fig


def convert_to_csv(data):
    """DataFrame을 UTF-8 BOM CSV 파일로 변환합니다."""
    return data.to_csv().encode("utf-8-sig")


# ---------------------------------------------------------
# 헤더
# ---------------------------------------------------------
st.title("📈 글로벌 주요 주식 대시보드")

st.caption(
    "Yahoo Finance 데이터를 이용해 글로벌 주요 종목의 주가, "
    "수익률, 거래량 및 캔들스틱 차트를 확인합니다."
)


# ---------------------------------------------------------
# 사이드바
# ---------------------------------------------------------
with st.sidebar:
    st.header("대시보드 설정")

    selected_region = st.selectbox(
        "시장 선택",
        options=list(STOCK_GROUPS.keys()),
        index=0,
    )

    region_stocks = STOCK_GROUPS[selected_region]
    region_labels = list(region_stocks.keys())

    default_count = min(4, len(region_labels))

    selected_stock_names = st.multiselect(
        "비교할 종목 선택",
        options=region_labels,
        default=region_labels[:default_count],
        help="너무 많은 종목을 동시에 선택하면 조회 속도가 느려질 수 있습니다.",
    )

    custom_tickers = st.text_input(
        "사용자 티커 추가",
        placeholder="예: AMD, TSM, 035420.KS",
        help="여러 티커를 쉼표로 구분해 입력하세요.",
    )

    period_label = st.selectbox(
        "조회 기간",
        options=list(PERIOD_OPTIONS.keys()),
        index=4,
    )

    interval_label = st.selectbox(
        "데이터 간격",
        options=list(INTERVAL_OPTIONS.keys()),
        index=0,
    )

    show_ma20 = st.checkbox(
        "20일 이동평균선",
        value=True,
    )

    show_ma60 = st.checkbox(
        "60일 이동평균선",
        value=True,
    )

    st.divider()

    if st.button(
        "데이터 새로고침",
        use_container_width=True,
        type="primary",
    ):
        st.cache_data.clear()
        st.rerun()

    st.caption("데이터는 일정 시간 캐시된 후 자동으로 갱신됩니다.")


# ---------------------------------------------------------
# 선택 티커 정리
# ---------------------------------------------------------
selected_tickers = {
    stock_name: region_stocks[stock_name]
    for stock_name in selected_stock_names
}

if custom_tickers.strip():
    parsed_custom_tickers = [
        ticker.strip().upper()
        for ticker in custom_tickers.split(",")
        if ticker.strip()
    ]

    for ticker in parsed_custom_tickers:
        selected_tickers[ticker] = ticker


if not selected_tickers:
    st.warning("사이드바에서 하나 이상의 종목을 선택해 주세요.")
    st.stop()


period = PERIOD_OPTIONS[period_label]
interval = INTERVAL_OPTIONS[interval_label]


# ---------------------------------------------------------
# 데이터 조회
# ---------------------------------------------------------
stock_data = {}
stock_metadata = {}
failed_tickers = []

with st.spinner("Yahoo Finance에서 주식 데이터를 불러오는 중입니다..."):
    for display_name, ticker in selected_tickers.items():
        try:
            data = load_stock_data(
                ticker=ticker,
                period=period,
                interval=interval,
            )

            if data.empty:
                failed_tickers.append(ticker)
                continue

            stock_data[display_name] = {
                "ticker": ticker,
                "data": data,
            }

            stock_metadata[display_name] = load_ticker_metadata(ticker)

        except Exception:
            failed_tickers.append(ticker)


if failed_tickers:
    st.warning(
        "다음 티커의 데이터를 불러오지 못했습니다: "
        + ", ".join(failed_tickers)
    )


if not stock_data:
    st.error(
        "조회 가능한 데이터가 없습니다. "
        "티커가 정확한지 확인하거나 다른 기간을 선택해 주세요."
    )
    st.stop()


# ---------------------------------------------------------
# 주요 종목 선택
# ---------------------------------------------------------
available_names = list(stock_data.keys())

focus_name = st.selectbox(
    "상세 분석 종목",
    options=available_names,
    index=0,
)

focus_ticker = stock_data[focus_name]["ticker"]
focus_data = stock_data[focus_name]["data"]
focus_metadata = stock_metadata.get(
    focus_name,
    {
        "name": focus_name,
        "currency": "",
        "exchange": "",
        "sector": "",
        "industry": "",
    },
)

focus_metrics = calculate_metrics(focus_data)
currency_symbol = get_currency_symbol(focus_metadata["currency"])


# ---------------------------------------------------------
# 상세 종목 헤더
# ---------------------------------------------------------
company_title = focus_metadata["name"]

st.subheader(f"{company_title} · {focus_ticker}")

metadata_parts = []

if focus_metadata["exchange"]:
    metadata_parts.append(f"거래소: {focus_metadata['exchange']}")

if focus_metadata["currency"]:
    metadata_parts.append(f"통화: {focus_metadata['currency']}")

if focus_metadata["sector"]:
    metadata_parts.append(f"섹터: {focus_metadata['sector']}")

if focus_metadata["industry"]:
    metadata_parts.append(f"산업: {focus_metadata['industry']}")

if metadata_parts:
    st.caption(" | ".join(metadata_parts))


# ---------------------------------------------------------
# 주요 지표
# ---------------------------------------------------------
metric_columns = st.columns(5)

with metric_columns[0]:
    st.metric(
        label="현재가",
        value=(
            f"{currency_symbol}"
            f"{format_number(focus_metrics['current_price'])}"
        ),
        delta=format_percentage(focus_metrics["daily_change"]),
    )

with metric_columns[1]:
    st.metric(
        label=f"{period_label} 수익률",
        value=format_percentage(focus_metrics["period_return"]),
    )

with metric_columns[2]:
    st.metric(
        label="기간 최고가",
        value=(
            f"{currency_symbol}"
            f"{format_number(focus_metrics['period_high'])}"
        ),
    )

with metric_columns[3]:
    st.metric(
        label="기간 최저가",
        value=(
            f"{currency_symbol}"
            f"{format_number(focus_metrics['period_low'])}"
        ),
    )

with metric_columns[4]:
    st.metric(
        label="연환산 변동성",
        value=(
            f"{format_number(focus_metrics['annual_volatility'])}%"
            if focus_metrics["annual_volatility"] is not None
            else "-"
        ),
    )


# ---------------------------------------------------------
# 상세 차트 탭
# ---------------------------------------------------------
price_tab, candle_tab, volume_tab, data_tab = st.tabs(
    [
        "주가 추이",
        "캔들스틱",
        "거래량",
        "원본 데이터",
    ]
)

with price_tab:
    price_fig = create_price_chart(
        data=focus_data,
        ticker_name=company_title,
        show_ma20=show_ma20,
        show_ma60=show_ma60,
    )

    st.plotly_chart(
        price_fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": True,
        },
    )

with candle_tab:
    if interval == "1mo" and len(focus_data) < 2:
        st.info("캔들스틱을 표시하기에 데이터가 충분하지 않습니다.")
    else:
        candle_fig = create_candlestick_chart(
            data=focus_data,
            ticker_name=company_title,
        )

        st.plotly_chart(
            candle_fig,
            use_container_width=True,
            config={
                "displaylogo": False,
                "scrollZoom": True,
            },
        )

with volume_tab:
    volume_fig = create_volume_chart(
        data=focus_data,
        ticker_name=company_title,
    )

    st.plotly_chart(
        volume_fig,
        use_container_width=True,
        config={
            "displaylogo": False,
        },
    )

with data_tab:
    display_data = focus_data.copy()
    display_data.index = display_data.index.strftime("%Y-%m-%d")
    display_data.index.name = "Date"

    st.dataframe(
        display_data.sort_index(ascending=False),
        use_container_width=True,
    )

    st.download_button(
        label="CSV 파일 다운로드",
        data=convert_to_csv(display_data),
        file_name=(
            f"{focus_ticker}_"
            f"{period}_"
            f"{datetime.now().strftime('%Y%m%d')}.csv"
        ),
        mime="text/csv",
    )


# ---------------------------------------------------------
# 종목 비교
# ---------------------------------------------------------
st.divider()
st.header("🌍 선택 종목 비교")

comparison_series = {}
ranking_rows = []

for display_name, item in stock_data.items():
    data = item["data"]
    ticker = item["ticker"]

    adjusted_close = data["Adj Close"].dropna()

    if adjusted_close.empty:
        continue

    first_price = adjusted_close.iloc[0]
    last_price = adjusted_close.iloc[-1]

    if first_price == 0:
        continue

    normalized = adjusted_close / first_price * 100
    comparison_series[f"{display_name} ({ticker})"] = normalized

    total_return = (last_price / first_price - 1) * 100
    daily_returns = adjusted_close.pct_change().dropna()

    volatility = (
        daily_returns.std() * (252 ** 0.5) * 100
        if not daily_returns.empty
        else None
    )

    ranking_rows.append(
        {
            "종목": display_name,
            "티커": ticker,
            "기간 수익률(%)": total_return,
            "연환산 변동성(%)": volatility,
            "시작 가격": first_price,
            "최근 가격": last_price,
        }
    )


if comparison_series:
    comparison_data = pd.concat(
        comparison_series,
        axis=1,
    ).sort_index()

    comparison_data.index.name = "Date"

    comparison_fig = create_comparison_chart(comparison_data)

    st.plotly_chart(
        comparison_fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": True,
        },
    )


# ---------------------------------------------------------
# 수익률 순위
# ---------------------------------------------------------
if ranking_rows:
    ranking_data = pd.DataFrame(ranking_rows)
    ranking_data = ranking_data.sort_values(
        by="기간 수익률(%)",
        ascending=False,
    ).reset_index(drop=True)

    ranking_data.index = ranking_data.index + 1
    ranking_data.index.name = "순위"

    left_column, right_column = st.columns([1, 1.35])

    with left_column:
        ranking_fig = px.bar(
            ranking_data.sort_values(
                by="기간 수익률(%)",
                ascending=True,
            ),
            x="기간 수익률(%)",
            y="종목",
            orientation="h",
            title=f"{period_label} 수익률 순위",
            text="기간 수익률(%)",
        )

        ranking_fig.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside",
            hovertemplate=(
                "종목: %{y}<br>"
                "기간 수익률: %{x:.2f}%"
                "<extra></extra>"
            ),
        )

        ranking_fig.add_vline(
            x=0,
            line_dash="dash",
        )

        ranking_fig.update_layout(
            height=max(400, len(ranking_data) * 55),
            margin=dict(l=20, r=40, t=60, b=20),
            showlegend=False,
        )

        st.plotly_chart(
            ranking_fig,
            use_container_width=True,
            config={
                "displaylogo": False,
            },
        )

    with right_column:
        st.subheader("성과 요약")

        formatted_ranking = ranking_data.copy()

        for column in [
            "기간 수익률(%)",
            "연환산 변동성(%)",
            "시작 가격",
            "최근 가격",
        ]:
            formatted_ranking[column] = formatted_ranking[column].round(2)

        st.dataframe(
            formatted_ranking,
            use_container_width=True,
            height=min(500, 42 + len(formatted_ranking) * 35),
        )

        st.download_button(
            label="비교 결과 CSV 다운로드",
            data=convert_to_csv(ranking_data),
            file_name=(
                f"global_stock_comparison_"
                f"{datetime.now().strftime('%Y%m%d')}.csv"
            ),
            mime="text/csv",
        )


# ---------------------------------------------------------
# 안내
# ---------------------------------------------------------
st.divider()

st.info(
    "본 대시보드는 Yahoo Finance에서 제공되는 데이터를 시각화한 "
    "정보 제공용 서비스입니다. 실제 시세와 차이가 있거나 데이터가 "
    "지연될 수 있으며, 투자 판단의 근거로 사용하기 전에 별도의 확인이 필요합니다."
)
