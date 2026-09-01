"""
Polymarket API package.

Modules
-------
gamma
    Event, market, tag, series, sports and search APIs.

clob
    Prices, order books, spreads, price history and rewards.

data_api
    Wallet profiles, positions, activity, trades and leaderboard.

ws_client
    Real-time WebSocket market data client.
"""

from .gamma import GammaAPI
from .clob import CLOBAPI
from .data_api import DataAPI

__all__ = [
    "GammaAPI",
    "CLOBAPI",
    "DataAPI",
]
