"""
Polymarket API package.

Clients:
- GammaClient
- CLOBClient
- DataAPIClient
- WebSocketClient
"""

from .gamma import GammaClient
from .clob import CLOBClient
from .data_api import DataAPIClient

try:
    from .ws_client import WebSocketClient
except ImportError:
    WebSocketClient = None


__all__ = [
    "GammaClient",
    "CLOBClient",
    "DataAPIClient",
    "WebSocketClient",
]
