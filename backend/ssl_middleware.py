"""
ASGI middleware to extract and inject client certificate into the scope.
Works at the raw ASGI level to have access to transport.
"""

import logging
from typing import Callable

logger = logging.getLogger(__name__)


class TransportCertificateMiddleware:
    """Raw ASGI middleware for SSL cert extraction."""

    def __init__(self, app: Callable) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] == "http":
            print(f"\n[ASGI] {scope.get('method')} {scope.get('path')}")
            print(f"[ASGI] Scope keys: {list(scope.keys())}")

            # In ASGI 3.0, transport should always exist
            # Try to access it and print all values
            for key in ["transport", "client", "server", "extensions"]:
                val = scope.get(key)
                print(f"[ASGI] scope['{key}']: {type(val).__name__ if val else 'None'}")

        await self.app(scope, receive, send)


class ClientCertificateMiddleware:
    """Deprecated: Use TransportCertificateMiddleware instead."""
    def __init__(self, app: Callable) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        await self.app(scope, receive, send)
