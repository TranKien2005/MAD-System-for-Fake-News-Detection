"""
Centralized rate-limiting and retry utilities for NIM API calls.

NIM (via 9router) has per-minute rate limits. When exceeded, it returns:
  - HTTP 429 (standard rate limit)
  - HTTP 401 with message "reset after Xm" (NIM-specific lockout)

This module provides:
  1. safe_invoke() — retry wrapper for LLM calls with exponential backoff
  2. RateLimiter — optional proactive throttle to prevent hitting limits
"""

import re
import time
import logging
import threading
from config.settings import config

logger = logging.getLogger(__name__)

# Default rate limiter instance (initialized at the bottom of the file)


def safe_invoke(llm, messages, max_retries=10, initial_delay=8, rate_limiter=None):
    """
    Invoke LLM with automatic retry on rate-limit errors.
    
    Handles both standard 429 errors and NIM's 401-based lockout
    with "reset after Xm" messages.
    
    Args:
        llm: LangChain LLM instance
        messages: List of messages to send
        max_retries: Maximum number of retry attempts (default: 10)
        initial_delay: Initial delay in seconds before first retry (default: 8)
        rate_limiter: Optional RateLimiter instance for proactive throttling
    
    Returns:
        LLM response object
    
    Raises:
        Last exception if all retries exhausted
    """
    delay = initial_delay
    last_exception = None
    
    # Use global default limiter if none provided
    limiter = rate_limiter or default_limiter
    
    for attempt in range(max_retries):
        if limiter:
            limiter.wait()
            
        try:
            return llm.invoke(messages)
        except Exception as e:
            last_exception = e
            error_str = str(e)
            
            # Check if this is a rate-limit related error
            is_rate_limit = _is_rate_limit_error(error_str)
            
            if is_rate_limit and attempt < max_retries - 1:
                # Try to extract the reset time from error message
                wait_time = _extract_reset_time(error_str)
                if wait_time is None:
                    wait_time = delay
                
                logger.warning(
                    f"Rate limit hit (attempt {attempt + 1}/{max_retries}). "
                    f"Waiting {wait_time}s before retry... "
                    f"Error: {error_str[:200]}"
                )
                time.sleep(wait_time)
                
                # Exponential backoff: increase delay for next attempt
                delay = min(delay * 2, 300)  # Cap at 5 minutes
                continue
            
            # Non-rate-limit error or last attempt — re-raise
            raise e
    
    # Should not reach here, but just in case
    raise last_exception


def _is_rate_limit_error(error_str: str) -> bool:
    """Check if an error is related to rate limiting."""
    rate_limit_indicators = [
        "429",                    # Standard HTTP 429
        "rate limit",             # Explicit rate limit message
        "too many requests",      # Common rate limit message
        "reset after",            # NIM-specific lockout message
        "quota exceeded",         # Quota-based limiting
        "resource exhausted",     # gRPC-style rate limit
    ]
    error_lower = error_str.lower()
    return any(indicator in error_lower for indicator in rate_limit_indicators)


def _extract_reset_time(error_str: str) -> float | None:
    """
    Extract the reset wait time from NIM error messages.
    
    Handles formats like:
      - "reset after 2m"  → 120s
      - "reset after 30s" → 30s
      - "reset after 1m30s" → 90s
      - "retry after 60 seconds" → 60s
    
    Returns:
        Wait time in seconds, or None if not found.
    """
    # Pattern: "reset after Xm" or "reset after XmYs"
    match = re.search(r'reset after (\d+)m(?:(\d+)s)?', error_str, re.IGNORECASE)
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2)) if match.group(2) else 0
        # Add a small buffer to ensure the reset has completed
        return minutes * 60 + seconds + 5
    
    # Pattern: "reset after Xs"
    match = re.search(r'reset after (\d+)s', error_str, re.IGNORECASE)
    if match:
        return int(match.group(1)) + 5
    
    # Pattern: "retry after X seconds"
    match = re.search(r'retry after (\d+)\s*seconds?', error_str, re.IGNORECASE)
    if match:
        return int(match.group(1)) + 5
    
    return None


class RateLimiter:
    """
    Proactive rate limiter to throttle API calls BEFORE hitting limits.
    
    Usage:
        limiter = RateLimiter(max_calls_per_minute=10)
        limiter.wait()  # Call before each API request
        response = llm.invoke(messages)
    """
    
    def __init__(self, max_calls_per_minute: int = 10):
        self.max_calls = max_calls_per_minute
        self.min_interval = 60.0 / max_calls_per_minute  # seconds between calls
        self._lock = threading.Lock()
        self._call_times: list[float] = []
    
    def wait(self):
        """Wait if necessary to stay within rate limits."""
        with self._lock:
            now = time.time()
            
            # Remove call times older than 1 minute
            cutoff = now - 60.0
            self._call_times = [t for t in self._call_times if t > cutoff]
            
            if len(self._call_times) >= self.max_calls:
                # We've hit the limit — wait until the oldest call expires
                oldest = self._call_times[0]
                wait_time = 60.0 - (now - oldest) + 1.0  # +1s buffer
                if wait_time > 0:
                    logger.info(f"Rate limiter: throttling for {wait_time:.1f}s ({len(self._call_times)}/{self.max_calls} calls in last minute)")
                    time.sleep(wait_time)
            elif self._call_times:
                # Ensure minimum interval between calls
                last = self._call_times[-1]
                elapsed = now - last
                if elapsed < self.min_interval:
                    wait_time = self.min_interval - elapsed
                    time.sleep(wait_time)
            
            self._call_times.append(time.time())
    
    def reset(self):
        """Reset the call history."""
        with self._lock:
            self._call_times.clear()


# Default rate limiter instance
default_limiter = RateLimiter(max_calls_per_minute=config.model.max_calls_per_minute)
