"""
Rate limiting functionality module.
"""

import time
# from collections import defaultdict
# from typing import Dict, Tuple


class RateLimiter:
    """Rate limiter for controlling request frequency."""

    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in the time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # IP -> list of timestamps

    def check_rate_limit(self, ip_address: str) -> bool:
        """
        Check if a request from an IP address is allowed.

        Args:
            ip_address: IP address of the client

        Returns:
            bool: True if request is allowed, False if rate limit exceeded
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Clean up old requests
        if ip_address in self.requests:
            self.requests[ip_address] = [
                ts for ts in self.requests[ip_address] if ts > window_start
            ]
        else:
            self.requests[ip_address] = []

        # Check if rate limit is exceeded
        if len(self.requests[ip_address]) >= self.max_requests:
            return False

        # Add new request
        self.requests[ip_address].append(now)
        return True

    def cleanup(self) -> None:
        """Clean up old request records."""
        current_time = time.time()
        for client_ip in list(self.requests.keys()):
            self.requests[client_ip] = [
                req_time
                for req_time in self.requests[client_ip]
                if current_time - req_time <= self.window_seconds
            ]
            if not self.requests[client_ip]:
                del self.requests[client_ip]
