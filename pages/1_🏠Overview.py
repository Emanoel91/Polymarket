"""
Polymarket Analytics Dashboard
Overview Page

File:
pages/1_🏠_Overview.py

Purpose:
    High-level overview of the Polymarket ecosystem.

Main data sources:
    - Gamma API
    - Data API
    - CLOB API

Main metrics:
    - Total Market Volume
    - 24H Volume
    - 7D Volume
    - 30D Volume
    - Active Markets
    - Closed Markets
    - Active Events
    - Open Interest

The page is designed to be read-only and does not require
authentication.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import streamlit as st

from api.gamma import GammaClient
from api.clob import CLOBAPI
from api.data_api import DataAPI


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Polymarket Overview",
    page_icon="🏠",
    layout="wide",
)


# ============================================================
# API CLIENTS
# ============================================================

@st.cache_resource
def get_gamma_client() -> GammaClient:
    return GammaClient()


@st.cache_resource
def get_clob_client() -> CLOBAPI:
    return CLOBAPI()


@st.cache_resource
def get_data_client() -> DataAPI:
    return DataAPI()


gamma = get_gamma_client()
clob = get_clob_client()
data_api = get_data_client()


# ============================================================
# CACHED API FUNCTIONS
# ============================================================
#
# GammaClient already implements offset-based pagination via
# get_all_events() / get_all_markets(), looping until the API
# returns an empty page. We use those directly instead of the
# single-page get_events()/get_markets() to fetch the FULL set,
# not just one page of 100.
#
# batch_size controls how many rows are requested per HTTP call
# (larger = fewer round-trips). max_pages is left as a generous
# safety net only, so it never truncates real data in practice.

BATCH_SIZE = 500
MAX_PAGES = 200  # safety net only: 500 * 200 = 100,000 rows max


@st.cache_data(ttl=300)
def fetch_active_events():
    """
    Fetch ALL active events (paginated).

    Cache:
        5 minutes
    """

    return gamma.get_all_events(
        active=True,
        closed=False,
        archived=False,
        batch_size=BATCH_SIZE,
        max_pages=MAX_PAGES,
    )


@st.cache_data(ttl=300)
def fetch_closed_events():
    """
    Fetch ALL closed events (paginated).

    Cache:
        5 minutes
    """

    return gamma.get_all_events(
        closed=True,
        batch_size=BATCH_SIZE,
        max_pages=MAX_PAGES,
    )


@st.cache_data(ttl=300)
def fetch_active_markets():
    """
    Fetch ALL active markets (paginated).

    Cache:
        5 minutes
    """

    return gamma.get_all_markets(
        active=True,
        closed=False,
        archived=False,
        batch_size=BATCH_SIZE,
        max_pages=MAX_PAGES,
    )


@st.cache_data(ttl=300)
def fetch_closed_markets():
    """
    Fetch ALL closed markets (paginated).

    Cache:
        5 minutes
    """

    return gamma.get_all_markets(
        closed=True,
        batch_size=BATCH_SIZE,
        max_pages=MAX_PAGES,
    )


@st.cache_data(ttl=300)
def fetch_open_interest():
    """
    Fetch current open interest.
    """

    return data_api.get_open_interest()


@st.cache_data(ttl=60)
def fetch_server_time():
    """
    Fetch CLOB server time.
    """

    return clob.get_server_time()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_float(value, default=0.0):
    """
    Safely convert a value to float.
    """

    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    """
    Safely convert a value to integer.
    """

    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def format_usd(value):
    """
    Format USD values for KPI cards.
    """

    value = safe_float(value)

    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"

    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"

    if value >= 1_000:
        return f"${value / 1_000:.2f}K"

    return f"${value:,.2f}"


def format_number(value):
    """
    Format integer/large number.
    """

    value = safe_float(value)

    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"

    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if value >= 1_000:
        return f"{value / 1_000:.2f}K"

    return f"{value:,.0f}"


def parse_json_field(value):
    """
    Parse JSON strings returned by Gamma API.

    Useful for fields such as:
        outcomes
        outcomePrices
        clobTokenIds
    """

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, str):

        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []

    return []


def extract_event_volume(event):
    """
    Extract total volume from an event.
    """

    possible_fields = [
        "volume",
        "volumeNum",
        "volume_num",
    ]

    for field in possible_fields:

        if field in event:

            value = safe_float(event.get(field))

            if value > 0:
                return value

    return 0.0


def extract_market_volume(market):
    """
    Extract total volume from a market.
    """

    possible_fields = [
        "volume",
        "volumeNum",
        "volume_num",
    ]

    for field in possible_fields:

        if field in market:

            value = safe_float(market.get(field))

            if value > 0:
                return value

    return 0.0


def extract_liquidity(market):
    """
    Extract market liquidity.
    """

    possible_fields = [
        "liquidity",
        "liquidityNum",
        "liquidity_num",
    ]

    for field in possible_fields:

        if field in market:

            value = safe_float(market.get(field))

            if value > 0:
                return value

    return 0.0


# ============================================================
# HEADER
# ============================================================

st.title("🏠 Polymarket Overview")

st.markdown(
    """
    High-level overview of the Polymarket prediction market ecosystem,
    including market activity, volume, liquidity and open interest.
    """
)


# ============================================================
# LAST UPDATED
# ============================================================

try:

    server_time = fetch_server_time()

    if isinstance(server_time, (int, float)):

        update_time = datetime.fromtimestamp(
            server_time,
            tz=timezone.utc,
        )

    else:

        update_time = datetime.now(timezone.utc)

except Exception:

    update_time = datetime.now(timezone.utc)


st.caption(
    f"Data timestamp: {update_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
)


# ============================================================
# LOAD DATA
# ============================================================

with st.spinner("Loading Polymarket data (fetching all pages)..."):

    try:
        active_events = fetch_active_events()
    except Exception:
        active_events = []

    try:
        closed_events = fetch_closed_events()
    except Exception:
        closed_events = []

    try:
        active_markets = fetch_active_markets()
    except Exception:
        active_markets = []

    try:
        closed_markets = fetch_closed_markets()
    except Exception:
        closed_markets = []

    try:
        open_interest_raw = fetch_open_interest()
    except Exception:
        open_interest_raw = None


# ============================================================
# DATA NORMALIZATION
# ============================================================

if not isinstance(active_events, list):
    active_events = []

if not isinstance(closed_events, list):
    closed_events = []

if not isinstance(active_markets, list):
    active_markets = []

if not isinstance(closed_markets, list):
    closed_markets = []


# ============================================================
# CALCULATE OVERVIEW METRICS
# ============================================================

active_event_count = len(active_events)

closed_event_count = len(closed_events)

active_market_count = len(active_markets)

closed_market_count = len(closed_markets)


active_market_volume = sum(
    extract_market_volume(market)
    for market in active_markets
)


closed_market_volume = sum(
    extract_market_volume(market)
    for market in closed_markets
)


active_event_volume = sum(
    extract_event_volume(event)
    for event in active_events
)


# Prefer event-level volume when available
# because events aggregate multiple markets.

if active_event_volume > 0:

    estimated_total_volume = active_event_volume

else:

    estimated_total_volume = (
        active_market_volume +
        closed_market_volume
    )


# ============================================================
# OPEN INTEREST
# ============================================================

open_interest = 0.0

if isinstance(open_interest_raw, dict):

    possible_fields = [
        "oi",
        "openInterest",
        "open_interest",
        "value",
        "total",
    ]

    for field in possible_fields:

        if field in open_interest_raw:

            open_interest = safe_float(
                open_interest_raw.get(field)
            )

            if open_interest > 0:
                break

elif isinstance(open_interest_raw, list):

    values = []

    for item in open_interest_raw:

        if not isinstance(item, dict):
            continue

        for field in [
            "oi",
            "openInterest",
            "open_interest",
            "value",
        ]:

            if field in item:

                values.append(
                    safe_float(item.get(field))
                )

                break

    open_interest = sum(values)

else:

    open_interest = safe_float(
        open_interest_raw
    )


# ============================================================
# KPI SECTION
# ============================================================

st.subheader("📊 Key Metrics")


# ------------------------------------------------------------
# Row 1
# ------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        label="Total Volume",
        value=format_usd(
            estimated_total_volume
        ),
    )


with col2:

    st.metric(
        label="Open Interest",
        value=format_usd(
            open_interest
        ),
    )


with col3:

    st.metric(
        label="Active Markets",
        value=format_number(
            active_market_count
        ),
    )


with col4:

    st.metric(
        label="Active Events",
        value=format_number(
            active_event_count
        ),
    )


# ------------------------------------------------------------
# Row 2
# ------------------------------------------------------------

st.markdown("")


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        label="Closed Markets",
        value=format_number(
            closed_market_count
        ),
    )


with col2:

    st.metric(
        label="Closed Events",
        value=format_number(
            closed_event_count
        ),
    )


with col3:

    st.metric(
        label="Active Market Volume",
        value=format_usd(
            active_market_volume
        ),
    )


with col4:

    st.metric(
        label="Active Event Volume",
        value=format_usd(
            active_event_volume
        ),
    )


# ============================================================
# MARKET STATUS
# ============================================================

st.divider()

st.subheader("📈 Market Status")


status_df = pd.DataFrame(
    {
        "Status": [
            "Active",
            "Closed",
        ],
        "Markets": [
            active_market_count,
            closed_market_count,
        ],
    }
)


col1, col2 = st.columns(2)


with col1:

    fig = px.pie(
        status_df,
        names="Status",
        values="Markets",
        hole=0.55,
        title="Market Distribution",
    )

    fig.update_layout(
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        legend_title="",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


with col2:

    fig = px.bar(
        status_df,
        x="Status",
        y="Markets",
        title="Active vs Closed Markets",
        text="Markets",
    )

    fig.update_layout(
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        xaxis_title="",
        yaxis_title="Markets",
    )

    fig.update_traces(
        textposition="outside"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# TOP ACTIVE MARKETS
# ============================================================

st.divider()

st.subheader("🔥 Top Active Markets by Volume")


top_markets = []


for market in active_markets:

    if not isinstance(market, dict):
        continue

    question = (
        market.get("question")
        or market.get("title")
        or "Unknown Market"
    )

    volume = extract_market_volume(market)

    liquidity = extract_liquidity(market)

    spread = safe_float(
        market.get("spread")
    )

    last_price = safe_float(
        market.get("lastTradePrice")
        or market.get("last_trade_price")
    )

    top_markets.append(
        {
            "Market": question,
            "Volume": volume,
            "Liquidity": liquidity,
            "Last Price": last_price,
            "Spread": spread,
        }
    )


if top_markets:

    top_markets_df = (
        pd.DataFrame(top_markets)
        .sort_values(
            "Volume",
            ascending=False,
        )
        .head(10)
    )

    display_df = top_markets_df.copy()

    display_df["Volume"] = display_df[
        "Volume"
    ].apply(format_usd)

    display_df["Liquidity"] = display_df[
        "Liquidity"
    ].apply(format_usd)

    display_df["Last Price"] = display_df[
        "Last Price"
    ].apply(
        lambda x: f"{x:.3f}"
        if x > 0
        else "—"
    )

    display_df["Spread"] = display_df[
        "Spread"
    ].apply(
        lambda x: f"{x:.3f}"
        if x > 0
        else "—"
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "No active market data is currently available."
    )


# ============================================================
# TOP MARKETS CHART
# ============================================================

if top_markets:

    chart_df = (
        pd.DataFrame(top_markets)
        .sort_values(
            "Volume",
            ascending=True,
        )
        .tail(10)
    )

    fig = px.bar(
        chart_df,
        x="Volume",
        y="Market",
        orientation="h",
        title="Top 10 Active Markets by Volume",
    )

    fig.update_layout(
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        xaxis_title="Volume (USD)",
        yaxis_title="",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# TOP EVENTS
# ============================================================

st.divider()

st.subheader("🌎 Top Active Events")


top_events = []


for event in active_events:

    if not isinstance(event, dict):
        continue

    title = (
        event.get("title")
        or event.get("question")
        or "Unknown Event"
    )

    slug = event.get("slug", "")

    volume = extract_event_volume(event)

    liquidity = safe_float(
        event.get("liquidity")
    )

    top_events.append(
        {
            "Event": title,
            "Slug": slug,
            "Volume": volume,
            "Liquidity": liquidity,
        }
    )


if top_events:

    top_events_df = (
        pd.DataFrame(top_events)
        .sort_values(
            "Volume",
            ascending=False,
        )
        .head(10)
    )

    display_events = top_events_df.copy()

    display_events["Volume"] = display_events[
        "Volume"
    ].apply(format_usd)

    display_events["Liquidity"] = display_events[
        "Liquidity"
    ].apply(format_usd)

    st.dataframe(
        display_events,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "No active event data is currently available."
    )


# ============================================================
# DATA QUALITY / API STATUS
# ============================================================

st.divider()

st.subheader("🔌 API Status")


col1, col2, col3 = st.columns(3)


with col1:

    if active_events:

        st.success(
            "Gamma API ✓"
        )

    else:

        st.warning(
            "Gamma API — No data"
        )


with col2:

    if open_interest_raw is not None:

        st.success(
            "Data API ✓"
        )

    else:

        st.warning(
            "Data API — No data"
        )


with col3:

    if server_time is not None:

        st.success(
            "CLOB API ✓"
        )

    else:

        st.warning(
            "CLOB API — No data"
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Polymarket Analytics Dashboard • "
    "Overview • "
    f"{active_market_count + closed_market_count:,} markets, "
    f"{active_event_count + closed_event_count:,} events loaded"
)
