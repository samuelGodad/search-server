"""
Utility functions module.
"""

import logging
import socket
from typing import Tuple


def setup_logging() -> logging.Logger:
    """
    Set up logging configuration.

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("search_server")
    logger.setLevel(logging.DEBUG)

    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger


def get_client_info(client_socket: socket.socket) -> Tuple[str, int]:
    """
    Get client IP address and port.

    Args:
        client_socket: Client socket object

    Returns:
        Tuple of (ip_address: str, port: int)
    """
    client_address = client_socket.getpeername()
    return client_address[0], client_address[1]


def format_debug_message(
    query: str, ip_address: str, execution_time: float, found: bool
) -> str:
    """
    Format debug message for logging.

    Args:
        query: Search query
        ip_address: Client IP address
        execution_time: Query execution time in milliseconds
        found: Whether the string was found

    Returns:
        Formatted debug message
    """
    return (
        f"DEBUG: Query='{query}' "
        f"IP={ip_address} "
        f"Time={execution_time:.2f}ms "
        f"Result={'STRING EXISTS' if found else 'STRING NOT FOUND'}"
    )
