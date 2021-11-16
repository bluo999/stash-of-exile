"""
Threads used in the application.
"""

import os
import time

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from threading import Condition
from typing import Callable, Deque, List, Optional, Tuple, Type, Union

from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QWidget

import log

from thread.ratelimiting import RateLimit, RateLimiter, TooManyReq


logger = log.get_logger(__name__)


IMAGE_CACHE_DIR = os.path.join('..', 'image_cache')


@dataclass
class Call:
    """Represents a service call and callback parameters."""

    service_method: Callable
    service_args: Tuple
    cb_obj: QWidget
    cb: Callable
    cb_args: Tuple = ()


@dataclass
class Ret:
    """Represents a service return and callback parameters."""

    cb_obj: QWidget
    cb: Callable
    cb_args: Tuple
    service_result: Tuple


class KillThread:
    """Represents a message to kill the thread."""


class ThreadManager(ABC):
    """
    Manager for a thread. Handles consuming messages from a queue, serving these
    calls and sending results to some callback.
    """

    def __init__(self, thread_type: Type['RetrieveThread']):
        self.queue: Deque[Union[Call, TooManyReq, KillThread]] = deque()
        self.cond = Condition()
        self.last_call: Optional[Call] = None
        self.thread: QThread = thread_type(self)
        self.thread.start()

    def kill_thread(self) -> None:
        """Kills the API thread."""
        self.cond.acquire()
        self.queue.append(KillThread())
        self.cond.notify()
        self.cond.release()
        self.thread.wait()

    def too_many_reqs(self, rate_limits_str: str, retry_after: int) -> None:
        """Updates the rate limits based on the string from response headers."""
        rate_limits: List[RateLimit] = []
        for rate_limit in rate_limits_str.split(','):
            hits, period, _ = rate_limit.split(':')
            rate_limits.append(RateLimit(int(hits), int(period) * 1000))
        self.cond.acquire()
        self.queue.appendleft(TooManyReq(rate_limits, retry_after))
        self.cond.notify()
        self.cond.release()

    def insert(self, calls: List) -> None:
        """Inserts a call into the queue."""
        self.cond.acquire()
        self.queue.extend(calls)
        self.cond.notify()
        self.cond.release()

    def retry_last(self) -> None:
        """Inserts the last API call popped into the front of the API queue."""
        if self.last_call is None:
            return
        self.cond.acquire()
        self.queue.appendleft(self.last_call)
        self.cond.notify()
        self.cond.release()

    def consume(self) -> Union[Ret, TooManyReq, KillThread]:
        """Consumes an element from the API queue (blocking)."""
        self.cond.acquire()
        while len(self.queue) == 0:
            self.cond.wait()

        ret = self.queue.popleft()
        # Special Signals
        if isinstance(ret, KillThread):
            return ret

        if isinstance(ret, TooManyReq):
            return ret

        # Process api method and store its result
        self.last_call = ret
        api_result = self.__getattribute__(ret.service_method.__name__)(
            *ret.service_args
        )

        self.cond.release()
        return Ret(ret.cb_obj, ret.cb, ret.cb_args, api_result)


class QThreadABCMeta(type(QThread), type(ABC)):
    """Final metatype for QThread and ABC."""


class RetrieveThread(QThread, ABC, metaclass=QThreadABCMeta):
    """QThread that will retrieve from some service."""

    def __init__(
        self, thread_manager: ThreadManager, rate_limiter: Optional[RateLimiter] = None
    ) -> None:
        QThread.__init__(self)
        self.thread_manager = thread_manager
        self.rate_limiter = rate_limiter

    def run(self) -> None:
        """Runs the thread."""
        while True:
            # Block and wait if there is a rate limiter
            if self.rate_limiter is not None:
                self.rate_limiter.block_until_ready()
            # Consume queue element (blocking if empty)
            ret = self.thread_manager.consume()

            # Add timestamp if there is a rate limiter
            if self.rate_limiter is not None:
                self.rate_limiter.insert()

            if isinstance(ret, KillThread):
                # Signal to exit the thread
                break

            if isinstance(ret, TooManyReq):
                if self.rate_limiter is None:
                    logger.error('Service received too many requests, exiting service')
                    break

                self.rate_limiter.update_rate_limits(ret.rate_limits)
                self.thread_manager.retry_last()
                logger.warning('Hit rate limit, sleeping for %s', ret.retry_after)
                time.sleep(ret.retry_after)
                continue

            self.service_success(ret)

    @abstractmethod
    def service_success(self, ret: Ret):
        """Callback for a successful service."""