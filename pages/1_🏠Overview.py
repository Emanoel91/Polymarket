# pages/1_🏠_Overview.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timezone

from api.gamma import GammaClient
from api.clob import CLOBClient
from api.data_api import DataAPIClient


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Polymarket Analytics — Overview",
    page_icon="🏠",
    layout="wide",
)


# ============================================================
# CLIENTS
# ============================================================

@st.cache_resource
def get_gamma_client():
    return GammaClient()


@st.cache_resource
def get_clob_client():
    return CLOBClient()


@st.cache_resource
def get_data_client():
    return DataAPIClient()


gamma = get_gamma_client()
clob = get_clob_client()
data_api = get_data_client()


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        if value is None:
            return default

        if isinstance(value, bool):
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def format_number(value):
    """Format large numbers in a readable way."""
    value = safe_float(value)

    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:.2f}K"

    return f"{value:,.0f}"


def format_usd(value):
    """Format USD values."""
    value = safe_float(value)

    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"

    if abs(value) >= 1_000:
        return f"${value / 1_000:.2f}K"

    return f"${value:,.2f}"


def extract_event_volume(event):
    """
    Extract event volume from different possible Gamma API fields.
    """
    if not isinstance(event, dict):
        return 0.0

    for key in [
        "volume",
        "volume24hr",
        "volume24h",
        "volumeNum",
        "volumeClob",
    ]:
        if key in event:
            value = safe_float(event.get(key))

            if value != 0:
                return value

    # Sometimes event volume is represented through markets.
    markets = event.get("markets", [])

    if isinstance(markets, list):
        total = 0.0

        for market in markets:
            total += extract_market_volume(market)

        return total

    return 0.0


def extract_market_volume(market):
    """
    Extract market volume from different possible Gamma API fields.
    """
    if not isinstance(market, dict):
        return 0.0

    for key in [
        "volume",
        "volumeNum",
        "volume24hr",
        "volume24h",
        "volumeClob",
    ]:
        if key in market:
            value = safe_float(market.get(key))

            if value != 0:
                return value

    return 0.0


def extract_liquidity(market):
    """
    Extract market liquidity from different possible Gamma API fields.
    """
    if not isinstance(market, dict):
        return 0.0

    for key in [
        "liquidity",
        "liquidityNum",
        "liquidityClob",
    ]:
        if key in market:
            value = safe_float(market.get(key))

            if value != 0:
                return value

    return 0.0


def get_market_question(market):
    """Return the best available market question/title."""
    if not isinstance(market, dict):
        return "Unknown Market"

    return (
        market.get("question")
        or market.get("title")
        or market.get("name")
        or "Unknown Market"
    )


def get_event_title(event):
    """Return the best available event title."""
    if not isinstance(event, dict):
        return "Unknown Event"

    return (
        event.get("title")
        or event.get("name")
        or event.get("question")
        or "Unknown Event"
    )


def is_active_market(market):
    """
    Determine whether a market is active.
    """
    if not isinstance(market, dict):
        return False

    return bool(market.get("active", False)) and not bool(
        market.get("closed", False)
    )


def is_closed_market(market):
    """
    Determine whether a market is closed.
    """
    if not isinstance(market, dict):
        return False

    return bool(market.get("closed", False))


def is_active_event(event):
    """
    Determine whether an event is active.
    """
    if not isinstance(event, dict):
        return False

    return bool(event.get("active", False)) and not bool(
        event.get("closed", False)
    )


def is_closed_event(event):
    """
    Determine whether an event is closed.
    """
    if not isinstance(event, dict):
        return False

    return bool(event.get("closed", False))


# ============================================================
# DATA LOADERS
# ============================================================

@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def load_active_events():
    """
    Load ALL active events using offset pagination.

    Pagination continues until the API returns an empty page.
    """
    return gamma.get_all_events(
        batch_size=100,
        active=True,
        closed=False,
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def load_closed_events():
    """
    Load ALL closed events using offset pagination.
    """
    return gamma.get_all_events(
        batch_size=100,
        closed=True,
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def load_active_markets():
    """
    Load ALL active markets using offset pagination.
    """
    return gamma.get_all_markets(
        batch_size=100,
        active=True,
        closed=False,
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def load_closed_markets():
    """
    Load ALL closed markets using offset pagination.
    """
    return gamma.get_all_markets(
        batch_size=100,
        closed=True,
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def load_clob_server_time():
    """
    Load CLOB server time.
    """
    return clob.get_server_time()


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def load_open_interest():
    """
    Load total open interest from Data API.

    If the endpoint is unavailable, return None so the
    dashboard can still load.
    """
    try:
        return data_api.get_open_interest()
    except Exception:
        return None


# ============================================================
# HEADER
# ============================================================

st.title("🏠 Polymarket Analytics")

st.markdown(
    """
    **Overview Dashboard**

    A high-level view of Polymarket events, markets, volume,
    liquidity and API connectivity.
    """
)


# ============================================================
# LOAD DATA
# ============================================================

active_events = []
closed_events = []
active_markets = []
closed_markets = []

event_error = None
closed_event_error = None
market_error = None
closed_market_error = None


# ------------------------------------------------------------
# Active Events
# ------------------------------------------------------------

try:
    with st.spinner("Loading all active events..."):
        active_events = load_active_events()

except Exception as e:
    event_error = str(e)


# ------------------------------------------------------------
# Closed Events
# ------------------------------------------------------------

try:
    with st.spinner("Loading all closed events..."):
        closed_events = load_closed_events()

except Exception as e:
    closed_event_error = str(e)


# ------------------------------------------------------------
# Active Markets
# ------------------------------------------------------------

try:
    with st.spinner("Loading all active markets..."):
        active_markets = load_active_markets()

except Exception as e:
    market_error = str(e)


# ------------------------------------------------------------
# Closed Markets
# ------------------------------------------------------------

try:
    with st.spinner("Loading all closed markets..."):
        closed_markets = load_closed_markets()

except Exception as e:
    closed_market_error = str(e)


# ============================================================
# ERROR DISPLAY
# ============================================================

if event_error:
    st.error(
        f"Unable to load active events:\n\n{event_error}"
    )

if closed_event_error:
    st.error(
        f"Unable to load closed events:\n\n{closed_event_error}"
    )

if market_error:
    st.error(
        f"Unable to load active markets:\n\n{market_error}"
    )

if closed_market_error:
    st.error(
        f"Unable to load closed markets:\n\n{closed_market_error}"
    )


# ============================================================
# DATA NORMALIZATION
# ============================================================

active_events = active_events if isinstance(active_events, list) else []
closed_events = closed_events if isinstance(closed_events, list) else []

active_markets = (
    active_markets
    if isinstance(active_markets, list)
    else []
)

closed_markets = (
    closed_markets
    if isinstance(closed_markets, list)
    else []
)


all_events = active_events + closed_events
all_markets = active_markets + closed_markets


# ============================================================
# BASIC METRICS
# ============================================================

total_events = len(all_events)
active_event_count = len(active_events)
closed_event_count = len(closed_events)

total_markets = len(all_markets)
active_market_count = len(active_markets)
closed_market_count = len(closed_markets)


total_market_volume = sum(
    extract_market_volume(market)
    for market in all_markets
)

active_market_volume = sum(
    extract_market_volume(market)
    for market in active_markets
)

closed_market_volume = sum(
    extract_market_volume(market)
    for market in closed_markets
)

total_liquidity = sum(
    extract_liquidity(market)
    for market in active_markets
)

total_event_volume = sum(
    extract_event_volume(event)
    for event in all_events
)


# ============================================================
# KPI ROW 1
# ============================================================

st.subheader("📊 Platform Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Events",
        format_number(total_events),
    )

with col2:
    st.metric(
        "Active Events",
        format_number(active_event_count),
    )

with col3:
    st.metric(
        "Total Markets",
        format_number(total_markets),
    )

with col4:
    st.metric(
        "Active Markets",
        format_number(active_market_count),
    )


# ============================================================
# KPI ROW 2
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Market Volume",
        format_usd(total_market_volume),
    )

with col2:
    st.metric(
        "Active Market Volume",
        format_usd(active_market_volume),
    )

with col3:
    st.metric(
        "Total Liquidity",
        format_usd(total_liquidity),
    )

with col4:
    st.metric(
        "Event Volume",
        format_usd(total_event_volume),
    )


# ============================================================
# STATUS SECTION
# ============================================================

st.divider()

st.subheader("📈 Market & Event Status")

col1, col2 = st.columns(2)


# ------------------------------------------------------------
# Market Status
# ------------------------------------------------------------

with col1:

    market_status_df = pd.DataFrame(
        {
            "Status": [
                "Active",
                "Closed",
            ],
            "Count": [
                active_market_count,
                closed_market_count,
            ],
        }
    )

    fig_market_status = px.pie(
        market_status_df,
        names="Status",
        values="Count",
        title="Markets by Status",
        hole=0.45,
    )

    fig_market_status.update_layout(
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        legend_title_text="",
    )

    st.plotly_chart(
        fig_market_status,
        use_container_width=True,
    )


# ------------------------------------------------------------
# Event Status
# ------------------------------------------------------------

with col2:

    event_status_df = pd.DataFrame(
        {
            "Status": [
                "Active",
                "Closed",
            ],
            "Count": [
                active_event_count,
                closed_event_count,
            ],
        }
    )

    fig_event_status = px.pie(
        event_status_df,
        names="Status",
        values="Count",
        title="Events by Status",
        hole=0.45,
    )

    fig_event_status.update_layout(
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        legend_title_text="",
    )

    st.plotly_chart(
        fig_event_status,
        use_container_width=True,
    )


# ============================================================
# TOP ACTIVE MARKETS
# ============================================================

st.divider()

st.subheader("🔥 Top Active Markets by Volume")


market_rows = []

for market in active_markets:

    market_rows.append(
        {
            "Market": get_market_question(market),
            "Volume": extract_market_volume(market),
            "Liquidity": extract_liquidity(market),
            "Active": market.get("active", False),
            "Closed": market.get("closed", False),
        }
    )


markets_df = pd.DataFrame(market_rows)


if not markets_df.empty:

    markets_df = markets_df.sort_values(
        "Volume",
        ascending=False,
    ).reset_index(drop=True)

    top_markets_df = markets_df.head(15).copy()

    chart_df = top_markets_df.copy()

    chart_df["Market"] = chart_df["Market"].apply(
        lambda x: (
            x[:70] + "..."
            if len(str(x)) > 70
            else str(x)
        )
    )

    fig_top_markets = px.bar(
        chart_df.sort_values(
            "Volume",
            ascending=True,
        ),
        x="Volume",
        y="Market",
        orientation="h",
        title="Top 15 Active Markets",
    )

    fig_top_markets.update_xaxes(
        tickprefix="$",
        separatethousands=True,
    )

    fig_top_markets.update_layout(
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        yaxis_title="",
        xaxis_title="Volume",
    )

    st.plotly_chart(
        fig_top_markets,
        use_container_width=True,
    )

    display_markets = top_markets_df.copy()

    display_markets["Volume"] = display_markets[
        "Volume"
    ].apply(format_usd)

    display_markets["Liquidity"] = display_markets[
        "Liquidity"
    ].apply(format_usd)

    display_markets = display_markets[
        [
            "Market",
            "Volume",
            "Liquidity",
            "Active",
            "Closed",
        ]
    ]

    st.dataframe(
        display_markets,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info("No active market data available.")


# ============================================================
# TOP EVENTS
# ============================================================

st.divider()

st.subheader("🔥 Top Events by Volume")


event_rows = []

for event in all_events:

    event_rows.append(
        {
            "Event": get_event_title(event),
            "Volume": extract_event_volume(event),
            "Active": is_active_event(event),
            "Closed": is_closed_event(event),
        }
    )


events_df = pd.DataFrame(event_rows)


if not events_df.empty:

    events_df = events_df.sort_values(
        "Volume",
        ascending=False,
    ).reset_index(drop=True)

    top_events_df = events_df.head(15).copy()

    chart_df = top_events_df.copy()

    chart_df["Event"] = chart_df["Event"].apply(
        lambda x: (
            x[:70] + "..."
            if len(str(x)) > 70
            else str(x)
        )
    )

    fig_top_events = px.bar(
        chart_df.sort_values(
            "Volume",
            ascending=True,
        ),
        x="Volume",
        y="Event",
        orientation="h",
        title="Top 15 Events",
    )

    fig_top_events.update_xaxes(
        tickprefix="$",
        separatethousands=True,
    )

    fig_top_events.update_layout(
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        yaxis_title="",
        xaxis_title="Volume",
    )

    st.plotly_chart(
        fig_top_events,
        use_container_width=True,
    )

    display_events = top_events_df.copy()

    display_events["Volume"] = display_events[
        "Volume"
    ].apply(format_usd)

    display_events = display_events[
        [
            "Event",
            "Volume",
            "Active",
            "Closed",
        ]
    ]

    st.dataframe(
        display_events,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info("No event data available.")


# ============================================================
# ACTIVE MARKET LIQUIDITY
# ============================================================

st.divider()

st.subheader("💧 Top Markets by Liquidity")


if not markets_df.empty:

    liquidity_df = markets_df.copy()

    liquidity_df = liquidity_df.sort_values(
        "Liquidity",
        ascending=False,
    ).head(15)

    chart_df = liquidity_df.copy()

    chart_df["Market"] = chart_df["Market"].apply(
        lambda x: (
            x[:70] + "..."
            if len(str(x)) > 70
            else str(x)
        )
    )

    fig_liquidity = px.bar(
        chart_df.sort_values(
            "Liquidity",
            ascending=True,
        ),
        x="Liquidity",
        y="Market",
        orientation="h",
        title="Top 15 Markets by Liquidity",
    )

    fig_liquidity.update_xaxes(
        tickprefix="$",
        separatethousands=True,
    )

    fig_liquidity.update_layout(
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        yaxis_title="",
        xaxis_title="Liquidity",
    )

    st.plotly_chart(
        fig_liquidity,
        use_container_width=True,
    )


# ============================================================
# API STATUS
# ============================================================

st.divider()

st.subheader("🔌 API Status")


api_col1, api_col2, api_col3 = st.columns(3)


# ------------------------------------------------------------
# Gamma API
# ------------------------------------------------------------

with api_col1:

    if (
        not event_error
        and not closed_event_error
        and not market_error
        and not closed_market_error
    ):
        st.success("🟢 Gamma API — Connected")

    else:
        st.error("🔴 Gamma API — Error")


# ------------------------------------------------------------
# CLOB API
# ------------------------------------------------------------

with api_col2:

    try:

        server_time = load_clob_server_time()

        if server_time is not None:
            st.success("🟢 CLOB API — Connected")

        else:
            st.warning("🟡 CLOB API — No response")

    except Exception as e:

        st.error(
            f"🔴 CLOB API — Error\n\n{e}"
        )


# ------------------------------------------------------------
# Data API
# ------------------------------------------------------------

with api_col3:

    try:

        oi = load_open_interest()

        if oi is not None:
            st.success("🟢 Data API — Connected")

        else:
            st.warning("🟡 Data API — No OI response")

    except Exception as e:

        st.error(
            f"🔴 Data API — Error\n\n{e}"
        )


# ============================================================
# API DETAILS
# ============================================================

with st.expander("🔍 API Details"):

    st.write(
        {
            "Gamma API": "https://gamma-api.polymarket.com",
            "CLOB API": "https://clob.polymarket.com",
            "Data API": "https://data-api.polymarket.com",
            "Active Events Loaded": len(active_events),
            "Closed Events Loaded": len(closed_events),
            "Active Markets Loaded": len(active_markets),
            "Closed Markets Loaded": len(closed_markets),
        }
    )

    if server_time is not None:
        st.write(
            f"CLOB Server Time: `{server_time}`"
        )


# ============================================================
# DATA LOADING INFO
# ============================================================

st.divider()

st.caption(
    f"""
    Data loaded from Polymarket APIs •
    {len(active_events):,} active events •
    {len(closed_events):,} closed events •
    {len(active_markets):,} active markets •
    {len(closed_markets):,} closed markets
    """
)


# ============================================================
# REFRESH
# ============================================================

st.sidebar.divider()

if st.sidebar.button("🔄 Refresh API Data"):

    load_active_events.clear()
    load_closed_events.clear()
    load_active_markets.clear()
    load_closed_markets.clear()
    load_clob_server_time.clear()
    load_open_interest.clear()

    st.rerun()
