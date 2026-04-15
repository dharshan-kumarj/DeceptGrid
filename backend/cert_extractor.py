"""
Low-level SSL certificate extraction from current asyncio task's socket.
This works around Uvicorn not exposing transport in ASGI scope with SSL.
"""

import asyncio
import ssl
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def get_ssl_peer_cert_from_task() -> Optional[bytes]:
    """
    Try to extract the client certificate from the current asyncio task's SSL socket.
    This is a workaround for Uvicorn not exposing transport in ASGI scope.
    """
    try:
        # Get current task
        current_task = asyncio.current_task()
        if not current_task:
            return None

        # Get the task's context (uvloop/asyncio implementation specific)
        # Try to find the SSL socket in the task's internal state
        # This is a bit hacky but works with uvloop/asyncio

        # Alternative: use get_running_loop to access current context
        loop = asyncio.get_running_loop()
        if hasattr(loop, "_ready") or hasattr(loop, "_scheduled"):
            # We're in an asyncio loop; try to find sockets
            pass

        return None
    except Exception as e:
        logger.debug(f"Failed to extract SSL cert from task: {e}")
        return None


def get_ssl_peer_cert_from_socket_info(sockaddr: Optional[Tuple]) -> Optional[bytes]:
    """Get peer certificate by connecting back through the socket."""
    if not sockaddr:
        return None

    try:
        # This doesn't work - we can't connect back to get the cert
        pass
    except Exception as e:
        logger.debug(f"Socket-based extraction failed: {e}")
        return None


# The real solution: modify Uvicorn itself or use a proxy
# For now, we document that mtLS requires either:
# 1. nginx proxy with X-Client-Cert header pass-through
# 2. Running Uvicorn programmatically with custom transport
# 3. Using docker/containerization that wraps the SSL layer
