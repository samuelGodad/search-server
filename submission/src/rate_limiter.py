"""
Rate limiting functionality module.
"""
import time
from collections import defaultdict
from typing import Dict, Tuple


class RateLimiter:
    """Handles rate limiting for client connections."""

    def __init__(self, max_requests: int = 100, time_window: int = 60) -> None:
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in the time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> Tuple[bool, int]:
        """
        Check if a client request is allowed.

        Args:
            client_ip: Client's IP address

        Returns:
            Tuple of (is_allowed: bool, remaining_requests: int)
        """
        current_time = time.time()
        
        # Remove old requests outside the time window
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time <= self.time_window
        ]

        # Check if client has exceeded the rate limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return False, 0

        # Add current request
        self.requests[client_ip].append(current_time)
        
        # Calculate remaining requests
        remaining = self.max_requests - len(self.requests[client_ip])
        return True, remaining

    def cleanup(self) -> None:
        """Clean up old request records."""
        current_time = time.time()
        for client_ip in list(self.requests.keys()):
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time <= self.time_window
            ]
            if not self.requests[client_ip]:
                del self.requests[client_ip] 