from datetime import date, datetime, timedelta
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
    page_title="원화 대비 주요 통화 환율",
    page_icon="💱",
    layout="wide",
)


# =========================================================
# 환율 데이터 설정
# Yahoo Finance 티커는 대체로 '통화 1단위당 원화 가격'입니다.
# 예: USDKRW=X → 1달러당 원화
# =========================================================
CURRENCIES = {
    "미국 달러": {
        "ticker": "USDKRW=X",
        "code": "USD",
        "unit": "1달러",
        "display_unit": "원/달러",
        "multiplier": 1,
    },
    "유로": {
        "ticker": "EURKRW=X",
        "code": "EUR",
        "unit": "1유로",
        "display_unit": "원/유로",
        "multiplier": 1,
    },
    "일본 엔": {
        "ticker": "JPYKRW=X",
        "code": "JPY",
        "unit": "100엔",
        "display_unit": "원/100엔",
        "multiplier": 100,
    },
    "중국 위안": {
        "ticker": "CNYKRW=X",
        "code": "CNY",
        "unit": "1위안",
        "display_unit": "원/위안",
        "multiplier": 1,
    },
    "영국 파운드": {
        "ticker": "GBPKRW=X",
        "code": "GBP",
        "unit": "1파운드",
        "display_unit": "원/파운드",
        "multiplier": 1,
    },
    "스위스 프랑": {
        "ticker": "CHFKRW=X",
        "code": "CHF",
        "unit": "1프랑",
        "display_unit": "원/프랑",
        "multiplier": 1,
    },
    "호주 달러": {
        "ticker": "AUDKRW=X",
        "code": "AUD",
        "unit": "1호주달러",
        "display_unit": "원/호주달러",
        "multiplier": 1,
    },
    "캐나다 달러": {
        "ticker": "CADKRW=X",
        "code": "CAD",
        "unit": "1캐나다달러",
        "display_unit": "원/캐나다달러",
        "multiplier": 1,
    },
}


# =========================================================
# 주요 경제·지정학 사건
#
# start: 차트 표시 시작일
# end: 영역 표시 종료일
# point_date: 사건 영향 분석의 기준일
#
# 사건 날짜와 설명은 필요에 따라 수정하거나 추가할 수 있습니다.
# =========================================================
ECONOMIC_EVENTS = [
    {
        "name": "유럽 재정위기 심화",
        "short_name": "유럽 재정위기",
        "start": "2011-07-01",
        "end": "2012-07-26",
        "point_date": "2011-08-05",
        "category": "금융위기",
        "description": (
            "유로존 국가의 재정 불안과 유럽 금융시장 변동성이 "
            "확대된 시기입니다."
        ),
    },
    {
        "name": "미국 신용등급 강등",
        "short_name": "미국 신용등급 강등",
        "start": "2011-08-05",
        "end": "2011-08-15",
        "point_date": "2011-08-05",
        "category": "금융시장",
        "description": (
            "미국 국가신용등급 강등으로 글로벌 위험회피 심리가 "
            "급격히 높아진 시기입니다."
        ),
    },
    {
        "name": "테이퍼 탠트럼",
        "short_name": "테이퍼 탠트럼",
        "start": "2013-05-22",
        "end": "2013-09-18",
        "point_date": "2013-05-22",
        "category": "통화정책",
        "description": (
            "미국 연준의 양적완화 축소 가능성이 제기되면서 "
            "신흥국 통화와 금융시장이 흔들린 시기입니다."
        ),
    },
    {
        "name": "중국 위안화 평가절하",
        "short_name": "위안화 평가절하",
        "start": "2015-08-11",
        "end": "2015-08-31",
        "point_date": "2015-08-11",
        "category": "외환정책",
        "description": (
            "중국의 위안화 기준환율 조정으로 아시아 금융시장과 "
            "원화 변동성이 높아진 시기입니다."
        ),
    },
    {
        "name": "브렉시트 국민투표",
        "short_name": "브렉시트",
        "start": "2016-06-23",
        "end": "2016-07-15",
        "point_date": "2016-06-23",
        "category": "정치·경제",
        "description": (
            "영국의 유럽연합 탈퇴 결정으로 파운드와 유로를 중심으로 "
            "환율 변동성이 크게 확대된 시기입니다."
        ),
    },
    {
        "name": "미·중 무역전쟁",
        "short_name": "미·중 무역전쟁",
        "start": "2018-07-06",
        "end": "2020-01-15",
        "point_date": "2018-07-06",
        "category": "무역분쟁",
        "description": (
            "미국과 중국의 상호 관세 부과가 본격화되면서 "
            "위안화와 원화의 변동성이 확대된 시기입니다."
        ),
    },
    {
        "name": "코로나19 팬데믹",
        "short_name": "팬데믹",
        "start": "2020-03-11",
        "end": "2020-06-30",
        "point_date": "2020-03-11",
        "category": "팬데믹",
        "description": (
            "WHO가 코로나19를 팬데믹으로 규정한 이후 "
            "달러 유동성 선호와 글로벌 위험회피가 급격히 높아졌습니다."
        ),
    },
    {
        "name": "러시아의 우크라이나 전면 침공",
        "short_name": "러시아·우크라이나 전쟁",
        "start": "2022-02-24",
        "end": "2022-06-30",
        "point_date": "2022-02-24",
        "category": "전쟁",
        "description": (
            "에너지·원자재 가격 급등과 안전자산 선호가 "
            "외환시장에 영향을 준 시기입니다."
        ),
    },
    {
        "name": "미국 연준 고강도 금리 인상",
        "short_name": "미국 급격한 금리 인상",
        "start": "2022-03-16",
        "end": "2023-07-26",
        "point_date": "2022-03-16",
        "category": "통화정책",
        "description": (
            "미국 연준의 빠른 기준금리 인상으로 달러 강세와 "
            "한미 금리차 확대 우려가 나타난 시기입니다."
        ),
    },
    {
        "name": "영국 감세안 충격",
        "short_name": "영국 감세안 충격",
        "start": "2022-09-23",
        "end": "2022-10-20",
        "point_date": "2022-09-23",
        "category": "재정정책",
        "description": (
            "영국 대규모 감세안 발표 이후 파운드와 영국 국채시장이 "
            "급격한 변동을 보인 시기입니다."
        ),
    },
    {
        "name": "미국 지역은행 위기",
        "short_name": "미국 은행위기",
        "start": "2023-03-10",
        "end": "2023-05-01",
        "point_date": "2023-03-10",
        "category": "금융위기",
        "description": (
            "미국 지역은행 부실 우려와 금융시스템 불안이 "
            "안전자산 선호에 영향을 준 시기입니다."
        ),
    },
    {
        "name": "이스라엘·하마스 전쟁",
        "short_name": "중동전쟁",
        "start": "2023-10-07",
        "end": "2024-01-31",
        "point_date": "2023-10-07",
        "category": "전쟁",
        "description": (
            "중동지역의 지정학적 위험과 국제유가 불확실성이 "
            "확대된 시기입니다."
        ),
    },
    {
        "name": "일본은행 마이너스 금리 종료",
        "short_name": "일본 마이너스 금리 종료",
        "start": "2024-03-19",
        "end": "2024-04-30",
        "point_date": "2024-03-19",
        "category": "통화정책",
        "description": (
            "일본은행의 통화정책 정상화가 엔화와 아시아 통화에 "
            "영향을 준 시기입니다."
        ),
    },
    {
        "name": "미·이란 전쟁 및 호르무즈 리스크",
        "short_name": "미·이란 전쟁",
        "start": "2026-02-01",
        "end": "2026-12-31",
        "point_date": "2026-02-01",
        "category": "전쟁",
        "description": (
            "미국과 이란의 군사충돌 및 호르무즈 해협 불안으로 "
            "유가·인플레이션·안전자산 선호가 영향을 받는 시기입니다."
        ),
    },
]


FREQUENCY_OPTIONS = {
    "일별": "D",
    "주별": "W-FRI",
    "월별": "ME",
}


# =========================================================
# 데이터 조회
# =========================================================
@st.cache_data(ttl=3600, show_spinner=False)
def download_fx_data(ticker, start_date, end_date):
    """
    Yahoo Finance 환율 데이터를 조회합니다.

    1차로 yf.download()를 사용하고,
    실패하면 Ticker.history() 방식으로 재시도합니다.
    """

    data = pd.DataFrame()

    # yfinance의 end 날짜는 일반적으로 미포함이므로 하루를 추가합니다.
    adjusted_end = (
        pd.Timestamp(end_date)
        + pd.Timedelta(days=1)
    ).strftime("%Y-%m-%d")

    try:
        data = yf.download(
            tickers=ticker,
            start=start_date,
            end=adjusted_end,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
            timeout=30,
        )
    except Exception:
        data = pd.DataFrame()

    if data is None or data.empty:
        try:
            ticker_object = yf.Ticker(ticker)

            data = ticker_object.history(
                start=start_date,
                end=adjusted_end,
                interval="1d",
                auto_adjust=False,
                timeout=30,
            )
        except Exception:
            return pd.DataFrame()

    if data is None or data.empty:
        return pd.DataFrame()

    data = data.copy()

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

    price_column = None

    if "Adj Close" in data.columns:
        price_column = "Adj Close"
    elif "Close" in data.columns:
        price_column = "Close"

    if price_column is None:
        return pd.DataFrame()

    result = pd.DataFrame(
        index=data.index
    )

    result["Rate"] = pd.to_numeric(
        data[price_column],
        errors="coerce",
    )

    result = result.dropna(
        subset=["Rate"]
    )

    return result


def load_selected_currencies(
    selected_currencies,
    start_date,
    end_date,
):
    loaded_data = {}
    failed_currencies = []

    progress_bar = st.progress(0)
    progress_text = st.empty()

    total_count = len(selected_currencies)

    for index, currency_name in enumerate(
        selected_currencies
    ):
        information = CURRENCIES[currency_name]

        progress_text.caption(
            f"환율 데이터 조회 중: {currency_name}"
        )

        data = download_fx_data(
            ticker=information["ticker"],
            start_date=start_date,
            end_date=end_date,
        )

        if data.empty:
            failed_currencies.append(
                currency_name
            )
        else:
            data = data.copy()

            # 일본 엔은 1엔 가격을 100엔 가격으로 변환
            data["Rate"] = (
                data["Rate"]
                * information["multiplier"]
            )

            loaded_data[currency_name] = data

        progress_bar.progress(
            (index + 1) / total_count
        )

        time.sleep(0.05)

    progress_bar.empty()
    progress_text.empty()

    return loaded_data, failed_currencies


# =========================================================
# 데이터 가공
# =========================================================
def resample_series(series, frequency):
    """
    일별, 주별 또는 월별 마지막 관측치를 사용합니다.
    """

    if frequency == "D":
        return series

    return series.resample(
        frequency
    ).last().dropna()


def create_rate_dataframe(
    loaded_data,
    frequency,
):
    series_map = {}

    for currency_name, data in (
        loaded_data.items()
    ):
        series = data["Rate"].copy()

        series = resample_series(
            series,
            frequency,
        )

        series_map[currency_name] = series

    if not series_map:
        return pd.DataFrame()

    result = pd.concat(
        series_map,
        axis=1,
    ).sort_index()

    result.index.name = "Date"

    return result


def create_normalized_dataframe(
    rate_data,
):
    normalized = pd.DataFrame(
        index=rate_data.index
    )

    for column in rate_data.columns:
        series = rate_data[column].dropna()

        if series.empty:
            continue

        first_value = series.iloc[0]

        if first_value == 0:
            continue

        normalized[column] = (
            rate_data[column]
            / first_value
            * 100
        )

    normalized.index.name = "Date"

    return normalized


def create_annual_return_dataframe(
    rate_data,
):
    annual_last = (
        rate_data
        .resample("YE")
        .last()
    )

    annual_returns = (
        annual_last
        .pct_change()
        * 100
    )

    annual_returns.index = (
        annual_returns.index.year
    )

    annual_returns.index.name = "연도"

    return annual_returns.dropna(
        how="all"
    )


def find_nearest_value(
    series,
    target_date,
    direction="nearest",
):
    """
    지정일과 가장 가까운 환율을 찾습니다.
    """

    clean_series = series.dropna()

    if clean_series.empty:
        return None, None

    target = pd.Timestamp(target_date)

    if direction == "before":
        candidates = clean_series[
            clean_series.index <= target
        ]

        if candidates.empty:
            return None, None

        return (
            candidates.index[-1],
            candidates.iloc[-1],
        )

    if direction == "after":
        candidates = clean_series[
            clean_series.index >= target
        ]

        if candidates.empty:
            return None, None

        return (
            candidates.index[0],
            candidates.iloc[0],
        )

    distances = abs(
        clean_series.index - target
    )

    position = distances.argmin()

    return (
        clean_series.index[position],
        clean_series.iloc[position],
    )


def calculate_event_impact(
    daily_rate_data,
    selected_event_names,
    window_days,
):
    """
    사건 기준일 전후 일정 기간의 환율 변화를 계산합니다.

    양수는 해당 외화가 원화 대비 상승했다는 의미이며,
    이는 같은 외화 1단위를 사는 데 더 많은 원화가
    필요해졌다는 뜻입니다.
    """

    rows = []

    selected_events = [
        event
        for event in ECONOMIC_EVENTS
        if event["name"]
        in selected_event_names
    ]

    for event in selected_events:
        event_date = pd.Timestamp(
            event["point_date"]
        )

        before_target = (
            event_date
            - pd.Timedelta(
                days=window_days
            )
        )

        after_target = (
            event_date
            + pd.Timedelta(
                days=window_days
            )
        )

        for currency_name in (
            daily_rate_data.columns
        ):
            series = daily_rate_data[
                currency_name
            ].dropna()

            before_date, before_rate = (
                find_nearest_value(
                    series,
                    before_target,
                    direction="before",
                )
            )

            event_observation_date, event_rate = (
                find_nearest_value(
                    series,
                    event_date,
                    direction="after",
                )
            )

            after_date, after_rate = (
                find_nearest_value(
                    series,
                    after_target,
                    direction="after",
                )
            )

            if (
                before_rate is None
                or event_rate is None
                or after_rate is None
                or before_rate == 0
                or event_rate == 0
            ):
                continue

            before_to_event = (
                event_rate / before_rate - 1
            ) * 100

            event_to_after = (
                after_rate / event_rate - 1
            ) * 100

            total_change = (
                after_rate / before_rate - 1
            ) * 100

            rows.append(
                {
                    "사건": event["short_name"],
                    "사건 기준일": event_date.date(),
                    "통화": currency_name,
                    "사건 전 관측일": before_date.date(),
                    "사건일 관측일": (
                        event_observation_date.date()
                    ),
                    "사건 후 관측일": after_date.date(),
                    "사건 전 환율": before_rate,
                    "사건일 환율": event_rate,
                    "사건 후 환율": after_rate,
                    "사건 전→사건일(%)": (
                        before_to_event
                    ),
                    "사건일→사건 후(%)": (
                        event_to_after
                    ),
                    "전체 변화율(%)": total_change,
                }
            )

    return pd.DataFrame(rows)


# =========================================================
# 지표 계산
# =========================================================
def calculate_currency_metrics(series):
    clean_series = series.dropna()

    if clean_series.empty:
        return {}

    current_rate = clean_series.iloc[-1]

    previous_rate = (
        clean_series.iloc[-2]
        if len(clean_series) >= 2
        else current_rate
    )

    first_rate = clean_series.iloc[0]

    daily_change = (
        (current_rate / previous_rate - 1)
        * 100
        if previous_rate != 0
        else None
    )

    period_change = (
        (current_rate / first_rate - 1)
        * 100
        if first_rate != 0
        else None
    )

    daily_returns = (
        clean_series
        .pct_change()
        .dropna()
    )

    annual_volatility = (
        daily_returns.std()
        * (252 ** 0.5)
        * 100
        if not daily_returns.empty
        else None
    )

    max_rate = clean_series.max()
    min_rate = clean_series.min()

    max_date = clean_series.idxmax()
    min_date = clean_series.idxmin()

    return {
        "current_rate": current_rate,
        "daily_change": daily_change,
        "period_change": period_change,
        "annual_volatility": annual_volatility,
        "max_rate": max_rate,
        "max_date": max_date,
        "min_rate": min_rate,
        "min_date": min_date,
    }


# =========================================================
# 차트 보조 함수
# =========================================================
def get_visible_events(
    start_date,
    end_date,
    selected_event_names,
):
    visible_events = []

    start_timestamp = pd.Timestamp(
        start_date
    )

    end_timestamp = pd.Timestamp(
        end_date
    )

    for event in ECONOMIC_EVENTS:
        if event["name"] not in (
            selected_event_names
        ):
            continue

        event_start = pd.Timestamp(
            event["start"]
        )

        event_end = pd.Timestamp(
            event["end"]
        )

        if (
            event_end >= start_timestamp
            and event_start <= end_timestamp
        ):
            visible_events.append(event)

    return visible_events


def add_event_annotations(
    fig,
    events,
    show_event_areas,
):
    """
    Plotly 차트에 주요 사건을 세로선 또는 음영 영역으로 표시합니다.
    """

    annotation_levels = [
        1.00,
        0.93,
        0.86,
        0.79,
    ]

    for index, event in enumerate(events):
        event_start = pd.Timestamp(
            event["start"]
        )

        event_end = pd.Timestamp(
            event["end"]
        )

        if show_event_areas:
            fig.add_vrect(
                x0=event_start,
                x1=event_end,
                opacity=0.08,
                line_width=0,
                layer="below",
            )

        fig.add_vline(
            x=event_start,
            line_width=1,
            line_dash="dot",
        )

        level = annotation_levels[
            index % len(annotation_levels)
        ]

        fig.add_annotation(
            x=event_start,
            y=level,
            yref="paper",
            text=event["short_name"],
            showarrow=False,
            textangle=-90,
            xanchor="left",
            yanchor="top",
            font=dict(size=10),
        )

    return fig


# =========================================================
# 차트 생성
# =========================================================
def create_normalized_chart(
    normalized_data,
    events,
    show_event_areas,
):
    long_data = (
        normalized_data
        .reset_index()
        .melt(
            id_vars="Date",
            var_name="통화",
            value_name="정규화 환율",
        )
        .dropna()
    )

    fig = px.line(
        long_data,
        x="Date",
        y="정규화 환율",
        color="통화",
        title=(
            "원화 대비 주요 통화 환율 추이 "
            "— 시작일 = 100"
        ),
        labels={
            "Date": "날짜",
            "정규화 환율": "환율 지수",
        },
    )

    fig.add_hline(
        y=100,
        line_dash="dash",
        annotation_text="비교 시작점",
    )

    fig.update_traces(
        hovertemplate=(
            "%{x|%Y-%m-%d}<br>"
            "환율 지수: %{y:,.2f}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        height=680,
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=70,
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

    fig = add_event_annotations(
        fig,
        events,
        show_event_areas,
    )

    return fig


def create_actual_rate_chart(
    rate_data,
    currency_name,
    events,
    show_event_areas,
):
    information = CURRENCIES[
        currency_name
    ]

    series = rate_data[
        currency_name
    ].dropna()

    chart_data = pd.DataFrame(
        {
            "Date": series.index,
            "Rate": series.values,
        }
    )

    fig = px.line(
        chart_data,
        x="Date",
        y="Rate",
        title=(
            f"{currency_name} 실제 환율 "
            f"({information['display_unit']})"
        ),
        labels={
            "Date": "날짜",
            "Rate": information[
                "display_unit"
            ],
        },
    )

    fig.update_traces(
        line=dict(width=2.5),
        hovertemplate=(
            "%{x|%Y-%m-%d}<br>"
            f"{information['display_unit']}: "
            "%{y:,.2f}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        height=620,
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=70,
            b=20,
        ),
    )

    fig.update_xaxes(
        rangeslider_visible=True
    )

    fig = add_event_annotations(
        fig,
        events,
        show_event_areas,
    )

    return fig


def create_annual_return_heatmap(
    annual_returns,
):
    heatmap_data = (
        annual_returns
        .transpose()
    )

    fig = px.imshow(
        heatmap_data,
        text_auto=".1f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        color_continuous_midpoint=0,
        title="연도별 원화 대비 환율 등락률",
        labels={
            "x": "연도",
            "y": "통화",
            "color": "등락률(%)",
        },
    )

    fig.update_layout(
        height=max(
            420,
            len(heatmap_data) * 65,
        ),
        margin=dict(
            l=20,
            r=20,
            t=70,
            b=20,
        ),
    )

    return fig


def create_latest_change_chart(
    summary_data,
):
    chart_data = (
        summary_data
        .sort_values(
            by="조회기간 등락률(%)",
            ascending=True,
        )
        .copy()
    )

    fig = px.bar(
        chart_data,
        x="조회기간 등락률(%)",
        y="통화",
        orientation="h",
        title="조회기간 원화 대비 통화별 등락률",
        text="조회기간 등락률(%)",
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
        hovertemplate=(
            "통화: %{y}<br>"
            "등락률: %{x:.2f}%"
            "<extra></extra>"
        ),
    )

    fig.add_vline(
        x=0,
        line_dash="dash",
    )

    fig.update_layout(
        height=max(
            430,
            len(chart_data) * 55,
        ),
        margin=dict(
            l=20,
            r=50,
            t=70,
            b=20,
        ),
        showlegend=False,
    )

    return fig


def create_event_impact_chart(
    event_impact_data,
):
    chart_data = (
        event_impact_data
        .copy()
    )

    fig = px.bar(
        chart_data,
        x="사건",
        y="전체 변화율(%)",
        color="통화",
        barmode="group",
        title="주요 사건 전후 환율 변화",
        labels={
            "전체 변화율(%)": "환율 변화율",
        },
    )

    fig.add_hline(
        y=0,
        line_dash="dash",
    )

    fig.update_traces(
        hovertemplate=(
            "사건: %{x}<br>"
            "변화율: %{y:.2f}%"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        height=600,
        margin=dict(
            l=20,
            r=20,
            t=70,
            b=100,
        ),
        xaxis_tickangle=-35,
    )

    return fig


# =========================================================
# 표시 형식
# =========================================================
def format_number(value, digits=2):
    if value is None or pd.isna(value):
        return "-"

    return f"{value:,.{digits}f}"


def format_percent(value):
    if value is None or pd.isna(value):
        return "-"

    return f"{value:+.2f}%"


def dataframe_to_csv(dataframe):
    return dataframe.to_csv(
        index=True
    ).encode("utf-8-sig")


# =========================================================
# 화면 헤더
# =========================================================
st.title("💱 2010년 이후 원화 대비 주요 통화 환율")

st.caption(
    "미국 달러, 유로, 일본 엔, 중국 위안 등 주요 통화의 "
    "원화 환율과 주요 경제·지정학 사건을 함께 살펴봅니다."
)

st.info(
    "환율이 상승했다는 것은 해당 외화 1단위를 구매하는 데 "
    "더 많은 원화가 필요해졌다는 의미입니다. 즉, 일반적으로 "
    "해당 통화 대비 원화 가치가 하락한 것으로 해석할 수 있습니다."
)


# =========================================================
# 사이드바
# =========================================================
today = date.today()
default_start_date = date(2010, 1, 1)

with st.sidebar:
    st.header("환율 분석 설정")

    selected_currencies = st.multiselect(
        "비교 통화",
        options=list(
            CURRENCIES.keys()
        ),
        default=[
            "미국 달러",
            "유로",
            "일본 엔",
            "중국 위안",
            "영국 파운드",
        ],
        help=(
            "통화를 너무 많이 선택하면 "
            "차트가 복잡해질 수 있습니다."
        ),
    )

    selected_date_range = st.date_input(
        "조회 기간",
        value=(
            default_start_date,
            today,
        ),
        min_value=date(2010, 1, 1),
        max_value=today,
    )

    frequency_label = st.selectbox(
        "차트 데이터 간격",
        options=list(
            FREQUENCY_OPTIONS.keys()
        ),
        index=2,
        help=(
            "2010년 이후 전체 흐름은 월별 표시가 "
            "가장 보기 편합니다."
        ),
    )

    st.divider()

    st.subheader("주요 사건 표시")

    event_categories = sorted(
        {
            event["category"]
            for event in ECONOMIC_EVENTS
        }
    )

    selected_event_categories = (
        st.multiselect(
            "사건 유형",
            options=event_categories,
            default=event_categories,
        )
    )

    available_events = [
        event["name"]
        for event in ECONOMIC_EVENTS
        if event["category"]
        in selected_event_categories
    ]

    selected_event_names = st.multiselect(
        "표시할 사건",
        options=available_events,
        default=available_events,
    )

    show_event_areas = st.checkbox(
        "사건 기간을 음영으로 표시",
        value=True,
    )

    event_window_days = st.slider(
        "사건 영향 분석 기간",
        min_value=7,
        max_value=90,
        value=30,
        step=7,
        help=(
            "사건 기준일 전후 며칠간의 "
            "환율 변화를 계산할지 설정합니다."
        ),
    )

    st.divider()

    if st.button(
        "화면 다시 그리기",
        use_container_width=True,
        type="primary",
    ):
        st.rerun()

    st.caption(
        "환율 데이터는 1시간 동안 캐시됩니다."
    )


# =========================================================
# 선택값 검증
# =========================================================
if not selected_currencies:
    st.warning(
        "하나 이상의 통화를 선택해 주세요."
    )
    st.stop()


if (
    not isinstance(
        selected_date_range,
        tuple,
    )
    or len(selected_date_range) != 2
):
    st.warning(
        "조회 시작일과 종료일을 모두 선택해 주세요."
    )
    st.stop()


start_date, end_date = selected_date_range

if start_date >= end_date:
    st.warning(
        "종료일은 시작일보다 뒤여야 합니다."
    )
    st.stop()


frequency = FREQUENCY_OPTIONS[
    frequency_label
]


# =========================================================
# 데이터 조회
# =========================================================
with st.spinner(
    "Yahoo Finance에서 환율 데이터를 불러오는 중입니다..."
):
    loaded_data, failed_currencies = (
        load_selected_currencies(
            selected_currencies,
            start_date,
            end_date,
        )
    )


if failed_currencies:
    st.warning(
        "다음 통화의 데이터를 불러오지 못했습니다: "
        + ", ".join(failed_currencies)
        + "\n\nYahoo Finance의 일시적인 요청 제한일 수 있습니다."
    )


if not loaded_data:
    st.error(
        "조회 가능한 환율 데이터가 없습니다."
    )
    st.stop()


# 일별 데이터: 사건 영향 분석용
daily_rate_data = create_rate_dataframe(
    loaded_data,
    "D",
)

# 선택 간격 데이터: 차트 표시용
rate_data = create_rate_dataframe(
    loaded_data,
    frequency,
)

normalized_data = (
    create_normalized_dataframe(
        rate_data
    )
)

annual_returns = (
    create_annual_return_dataframe(
        daily_rate_data
    )
)

visible_events = get_visible_events(
    start_date,
    end_date,
    selected_event_names,
)


# =========================================================
# 최신 환율 요약
# =========================================================
summary_rows = []

for currency_name in (
    daily_rate_data.columns
):
    metrics = calculate_currency_metrics(
        daily_rate_data[currency_name]
    )

    information = CURRENCIES[
        currency_name
    ]

    summary_rows.append(
        {
            "통화": currency_name,
            "통화코드": information["code"],
            "현재 환율": metrics.get(
                "current_rate"
            ),
            "표시 단위": information[
                "display_unit"
            ],
            "일간 등락률(%)": metrics.get(
                "daily_change"
            ),
            "조회기간 등락률(%)": metrics.get(
                "period_change"
            ),
            "연환산 변동성(%)": metrics.get(
                "annual_volatility"
            ),
            "기간 최고 환율": metrics.get(
                "max_rate"
            ),
            "최고 환율일": metrics.get(
                "max_date"
            ),
            "기간 최저 환율": metrics.get(
                "min_rate"
            ),
            "최저 환율일": metrics.get(
                "min_date"
            ),
        }
    )


summary_data = pd.DataFrame(
    summary_rows
)

summary_data = summary_data.sort_values(
    by="조회기간 등락률(%)",
    ascending=False,
).reset_index(drop=True)


st.header("📌 현재 환율 요약")

metric_columns = st.columns(
    min(4, len(summary_data))
)

for index in range(
    min(4, len(summary_data))
):
    row = summary_data.iloc[index]

    with metric_columns[index]:
        st.metric(
            label=(
                f"{row['통화']} "
                f"({row['표시 단위']})"
            ),
            value=format_number(
                row["현재 환율"],
                2,
            ),
            delta=format_percent(
                row["일간 등락률(%)"]
            ),
        )


if len(summary_data) > 4:
    second_metric_columns = st.columns(
        min(
            4,
            len(summary_data) - 4,
        )
    )

    for display_index, row_index in (
        enumerate(
            range(
                4,
                min(8, len(summary_data)),
            )
        )
    ):
        row = summary_data.iloc[
            row_index
        ]

        with second_metric_columns[
            display_index
        ]:
            st.metric(
                label=(
                    f"{row['통화']} "
                    f"({row['표시 단위']})"
                ),
                value=format_number(
                    row["현재 환율"],
                    2,
                ),
                delta=format_percent(
                    row["일간 등락률(%)"]
                ),
            )


# =========================================================
# 주요 차트
# =========================================================
st.divider()
st.header("🌍 주요 통화 환율 동향")

(
    normalized_tab,
    actual_tab,
    annual_tab,
    ranking_tab,
) = st.tabs(
    [
        "한눈에 비교",
        "실제 환율",
        "연도별 등락률",
        "통화별 순위",
    ]
)


with normalized_tab:
    st.plotly_chart(
        create_normalized_chart(
            normalized_data,
            visible_events,
            show_event_areas,
        ),
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": True,
        },
    )

    st.caption(
        "모든 통화의 조회 시작일 환율을 100으로 환산했습니다. "
        "지수가 상승할수록 해당 통화가 원화 대비 강해졌다는 뜻입니다."
    )


with actual_tab:
    actual_currency = st.selectbox(
        "실제 환율을 확인할 통화",
        options=list(
            rate_data.columns
        ),
        key="actual_currency",
    )

    st.plotly_chart(
        create_actual_rate_chart(
            rate_data,
            actual_currency,
            visible_events,
            show_event_areas,
        ),
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": True,
        },
    )


with annual_tab:
    if annual_returns.empty:
        st.info(
            "연도별 등락률을 계산하기에 "
            "데이터 기간이 충분하지 않습니다."
        )
    else:
        st.plotly_chart(
            create_annual_return_heatmap(
                annual_returns
            ),
            use_container_width=True,
            config={
                "displaylogo": False,
            },
        )

        st.caption(
            "양수는 해당 통화가 원화 대비 상승한 연도, "
            "음수는 해당 통화가 원화 대비 하락한 연도입니다."
        )


with ranking_tab:
    st.plotly_chart(
        create_latest_change_chart(
            summary_data
        ),
        use_container_width=True,
        config={
            "displaylogo": False,
        },
    )


# =========================================================
# 주요 사건 분석
# =========================================================
st.divider()
st.header("🗓️ 주요 경제사건과 환율")

if not visible_events:
    st.info(
        "선택한 기간에 표시할 주요 사건이 없습니다."
    )
else:
    event_table = pd.DataFrame(
        [
            {
                "사건": event["name"],
                "시작일": event["start"],
                "종료일": event["end"],
                "유형": event["category"],
                "설명": event["description"],
            }
            for event in visible_events
        ]
    )

    st.dataframe(
        event_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "설명": st.column_config.TextColumn(
                width="large"
            ),
        },
    )


event_impact_data = calculate_event_impact(
    daily_rate_data,
    selected_event_names,
    event_window_days,
)


if event_impact_data.empty:
    st.info(
        "선택한 사건의 영향 분석에 필요한 "
        "환율 데이터가 없습니다."
    )
else:
    (
        event_chart_tab,
        event_table_tab,
    ) = st.tabs(
        [
            "사건별 변화 차트",
            "사건별 상세 데이터",
        ]
    )

    with event_chart_tab:
        selected_impact_events = (
            st.multiselect(
                "비교할 사건",
                options=(
                    event_impact_data[
                        "사건"
                    ]
                    .drop_duplicates()
                    .tolist()
                ),
                default=(
                    event_impact_data[
                        "사건"
                    ]
                    .drop_duplicates()
                    .tolist()[-5:]
                ),
                key="impact_events",
            )
        )

        filtered_impact_data = (
            event_impact_data[
                event_impact_data[
                    "사건"
                ].isin(
                    selected_impact_events
                )
            ]
        )

        if filtered_impact_data.empty:
            st.info(
                "하나 이상의 사건을 선택해 주세요."
            )
        else:
            st.plotly_chart(
                create_event_impact_chart(
                    filtered_impact_data
                ),
                use_container_width=True,
                config={
                    "displaylogo": False,
                },
            )

            st.caption(
                f"사건 기준일 전후 약 {event_window_days}일의 "
                "환율 변화를 비교합니다. 양수는 해당 외화의 "
                "원화 대비 강세를 의미합니다."
            )

    with event_table_tab:
        impact_display = (
            event_impact_data.copy()
        )

        numeric_columns = [
            "사건 전 환율",
            "사건일 환율",
            "사건 후 환율",
            "사건 전→사건일(%)",
            "사건일→사건 후(%)",
            "전체 변화율(%)",
        ]

        for column in numeric_columns:
            impact_display[column] = (
                impact_display[column]
                .round(2)
            )

        st.dataframe(
            impact_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "사건 전→사건일(%)": (
                    st.column_config.NumberColumn(
                        format="%.2f%%"
                    )
                ),
                "사건일→사건 후(%)": (
                    st.column_config.NumberColumn(
                        format="%.2f%%"
                    )
                ),
                "전체 변화율(%)": (
                    st.column_config.NumberColumn(
                        format="%.2f%%"
                    )
                ),
            },
        )


# =========================================================
# 환율 요약표 및 다운로드
# =========================================================
st.divider()
st.header("📋 통화별 상세 요약")

summary_display = summary_data.copy()

numeric_summary_columns = [
    "현재 환율",
    "일간 등락률(%)",
    "조회기간 등락률(%)",
    "연환산 변동성(%)",
    "기간 최고 환율",
    "기간 최저 환율",
]

for column in numeric_summary_columns:
    summary_display[column] = (
        summary_display[column]
        .round(2)
    )

for date_column in [
    "최고 환율일",
    "최저 환율일",
]:
    summary_display[date_column] = (
        pd.to_datetime(
            summary_display[date_column]
        )
        .dt.strftime("%Y-%m-%d")
    )

st.dataframe(
    summary_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "일간 등락률(%)": (
            st.column_config.NumberColumn(
                format="%.2f%%"
            )
        ),
        "조회기간 등락률(%)": (
            st.column_config.NumberColumn(
                format="%.2f%%"
            )
        ),
        "연환산 변동성(%)": (
            st.column_config.NumberColumn(
                format="%.2f%%"
            )
        ),
    },
)


download_columns = (
    daily_rate_data.copy()
)

download_columns.index = (
    download_columns.index.strftime(
        "%Y-%m-%d"
    )
)

download_columns.index.name = "Date"

download_column, event_download_column = (
    st.columns(2)
)

with download_column:
    st.download_button(
        label="환율 시계열 CSV 다운로드",
        data=dataframe_to_csv(
            download_columns
        ),
        file_name=(
            "krw_exchange_rates_"
            f"{datetime.now().strftime('%Y%m%d')}.csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )

with event_download_column:
    if not event_impact_data.empty:
        st.download_button(
            label="사건 영향 분석 CSV 다운로드",
            data=event_impact_data.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name=(
                "fx_event_impact_"
                f"{datetime.now().strftime('%Y%m%d')}.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )


# =========================================================
# 해석 안내
# =========================================================
st.divider()

with st.expander("대시보드 해석 방법"):
    st.markdown(
        """
        ### 1. 환율 상승

        예를 들어 원·달러 환율이 1,200원에서 1,400원으로
        상승했다면 1달러를 구매하는 데 필요한 원화가
        많아진 것입니다. 이는 달러 대비 원화 가치가
        하락한 것으로 해석할 수 있습니다.

        ### 2. 정규화 환율

        조회 시작일의 환율을 모두 100으로 맞춘 값입니다.
        통화마다 실제 환율 수준과 단위가 다르기 때문에
        장기적인 상대 변화율을 한눈에 비교하는 데 적합합니다.

        ### 3. 일본 엔 환율

        Yahoo Finance의 원자료는 1엔당 원화 가격이지만,
        국내에서 일반적으로 사용하는 방식에 맞춰
        100엔당 원화 가격으로 환산했습니다.

        ### 4. 사건 영향 분석

        사건 전후 환율 변화는 단순한 시점 비교입니다.
        환율은 금리, 무역수지, 자본 이동, 경기 전망,
        중앙은행 정책 등 다양한 요인의 영향을 받으므로
        특정 사건이 환율 변동의 유일한 원인이라는 뜻은 아닙니다.
        """
    )


st.warning(
    "Yahoo Finance의 환율 데이터는 지연되거나 누락될 수 있습니다. "
    "현재 환율 확인이나 실제 외환 거래 전에는 은행 또는 공식 "
    "외환시장 자료를 별도로 확인해야 합니다."
)
