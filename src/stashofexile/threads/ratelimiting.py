"""
Handles rate limiting for Retrieve Threads.
"""

import collections
import dataclasses
import math
from datetime import datetime
from typing import List, NamedTuple, Optional

from stashofexile import log

logger = log.get_logger(__name__)


def get_time_ms() -> int:
    """
    Gets time in milliseconds (epoch doesn't matter since only used for relativity).
    """
    return round(datetime.utcnow().timestamp() * 1000)


class RateLimit(NamedTuple):
    """Represents a rate limit."""

    hits: int
    period: int


@dataclasses.dataclass
class TooManyReq:
    """Class storing data from a too many requests HTTP error."""

    rate_limits: List[RateLimit]
    retry_after: int


class RateQueue(collections.deque):
    """Queue that stores call timestamps for rate limiting purposes."""

    def __init__(self, hits: int = 0, period: int = 0):
        super().__init__()
        self.update_rate_limit(hits, period)

    def update_rate_limit(self, hits: int, period: int):
        """Update to new rate limits."""
        self.hits = hits
        self.period = period


class RateLimiter:
    """Rate limiter for a retrieve thread."""

    def __init__(self, rate_limits: List[RateLimit]):
        self.queues = [
            RateQueue(rate_limit.hits, rate_limit.period) for rate_limit in rate_limits
        ]

    def update_rate_limits(self, rate_limits: List[RateLimit]) -> None:
        """Update to new rate limits."""
        if len(rate_limits) < len(self.queues):
            self.queues = self.queues[: len(rate_limits)]
        elif len(rate_limits) > len(self.queues):
            for _ in range(len(rate_limits) - len(self.queues)):
                self.queues.append(RateQueue())

        for queue, rate_limit in zip(self.queues, rate_limits):
            queue.update_rate_limit(rate_limit.hits, rate_limit.period)

    def insert(self) -> None:
        """Add timestamp to queue."""
        for queue in self.queues:
            queue.append(get_time_ms())

    def get_sleep_time(self) -> Optional[int]:
        """
        Gets the sleep time such that the next API call won't be rejected. Returns None
        if not necessary.
        """
        if all(len(queue) < queue.hits for queue in self.queues):
            return None

        # Pop excess elements (needed when rate limits change)
        for queue in self.queues:
            num_iters = len(queue) - queue.hits
            for _ in range(num_iters):
                queue.popleft()

        assert all(len(queue) <= queue.hits for queue in self.queues)
        next_avail_time = max(
            queue.popleft() + queue.period
            for queue in self.queues
            if len(queue) == queue.hits
        )
        sleep_time = max(round((next_avail_time - get_time_ms()) / 1000), 0)
        if sleep_time > 0:
            return sleep_time

        return None
