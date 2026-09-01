"""
Main Streamlit application.

At this stage the dashboard only provides:
- API connectivity tests
- Basic Polymarket API overview
- Simple market discovery

The full analytical pages will be added later.
"""

import streamlit as st

from api.gamma import GammaAPI
from api.clob import CLOBAPI
from api.data_api import DataAPI


# ----------------------------------------------------------------------
# Page configuration
# ----------------------------------------------------------------------

st.set_page_config(
    page_title="Polymarket Analytics",
    page_icon="📊",
    layout="wide",
)


# ----------------------------------------------------------------------
# API clients
# ----------------------------------------------------------------------

@st.cache_resource
def get_gamma_client():
    return GammaAPI()


@st.cache_resource
def get_clob_client():
    return CLOBAPI()


@st.cache_resource
def get_data_client():
    return DataAPI()


gamma = get_gamma_client()
clob = get_clob_client()
data_api = get_data_client()


# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------

st.title("📊 Polymarket Analytics Dashboard")

st.markdown(
    """
    ### Welcome

    This dashboard is powered by the public Polymarket APIs.

    **Available API layers:**

    - Gamma API — Events & Markets
    - CLOB API — Prices & Order Books
    - Data API — Wallets, Positions & Activity
    - WebSocket — Real-time Market Data
    """
)


# ----------------------------------------------------------------------
# API Status
# ----------------------------------------------------------------------

st.subheader("🔌 API Connectivity")

col1, col2, col3 = st.columns(3)


# Gamma
with col1:

    try:

        events = gamma.get_events(
            limit=1,
            active=True,
        )

        st.success("Gamma API: Connected")

        if isinstance(events, list):
            st.metric(
                "Sample Events",
                len(events),
            )

    except Exception as exc:

        st.error("Gamma API: Error")
        st.caption(str(exc))


# CLOB
with col2:

    try:

        server_time = clob.get_server_time()

        st.success("CLOB API: Connected")

        st.write(
            f"Server Time: `{server_time}`"
        )

    except Exception as exc:

        st.error("CLOB API: Error")
        st.caption(str(exc))


# Data API
with col3:

    try:

        oi = data_api.get_open_interest()

        st.success("Data API: Connected")

        st.write(
            "Open Interest endpoint available."
        )

    except Exception as exc:

        st.error("Data API: Error")
        st.caption(str(exc))


# ----------------------------------------------------------------------
# Market Explorer Preview
# ----------------------------------------------------------------------

st.divider()

st.subheader("🔎 Market Explorer Preview")

limit = st.number_input(
    "Number of markets",
    min_value=1,
    max_value=100,
    value=10,
)


if st.button(
    "Load Active Markets",
    type="primary",
):

    try:

        markets = gamma.get_markets(
            limit=int(limit),
            active=True,
            closed=False,
        )

        if markets:

            st.dataframe(
                markets,
                use_container_width=True,
            )

        else:

            st.info(
                "No markets were returned."
            )

    except Exception as exc:

        st.error(
            f"Unable to load markets: {exc}"
        )


# ----------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------

st.divider()

st.caption(
    "Polymarket Analytics Dashboard • "
    "Powered by Polymarket public APIs"
)
