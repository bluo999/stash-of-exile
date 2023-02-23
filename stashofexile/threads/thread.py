"""
Threads used in the application.
"""

import abc
import collections
import dataclasses
import threading
import time
from typing import Callable, Deque, Iterable, List, NamedTuple, Optional, Tuple, Type

from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QWidget

from stashofexile import log
from stashofexile.threads import ratelimiting

logger = log.get_logger(__name__)


@dataclasses.dataclass
class Call:
    """Represents a service call and callback parameters."""

    service_method: Callable
    service_args: Tuple
    cb_obj: Optional[QWidget]
    cb: Callable = lambda: ()
    cb_args: Tuple = ()


@dataclasses.dataclass
class Ret:
    """Represents a service return and callback parameters."""

    cb_obj: Optional[QWidget]
    cb: Callable
    cb_args: Tuple
    service_result: Tuple


class KillThread:
    """Represents a message to kill the thread."""


Action = Call | ratelimiting.TooManyReq | KillThread


class QThreadABCMeta(type(QThread), type(abc.ABC)):
    """Final metatype for QThread and ABC."""


class RetrieveThread(QThread, abc.ABC, metaclass=QThreadABCMeta):
    """
    QThread that will retrieve from some service. Consumes messages from a
    queue, serving these calls and sending results to some callback.
    """

    def __init__(self, rate_limiter: Optional[ratelimiting.RateLimiter] = None) -> None:
        super().__init__()
        self.queue: Deque[Action] = collections.deque()
        self.cond = threading.Condition()
        self.last_call: Optional[Call] = None
        self.rate_limiter = rate_limiter
        self.start()

    def kill_thread(self) -> None:
        """KIlls the thread."""
        self.cond.acquire()
        self.queue.appendleft(KillThread())
        self.cond.notify()
        self.cond.release()
        self.wait()

    def too_many_reqs(
        self, rate_limits: List[ratelimiting.RateLimit], retry_after: int = 0
    ) -> None:
        """Updates the rate limits based on a new set of rate limits."""
        self.cond.acquire()
        self.queue.appendleft(ratelimiting.TooManyReq(rate_limits, retry_after))
        self.cond.notify()
        self.cond.release()

    def insert(self, calls: Iterable[Call]) -> None:
        """Inserts a call into the queue."""
        self.cond.acquire()
        self.queue.extend(calls)
        self.cond.notify()
        self.cond.release()

    def retry_last(self) -> None:
        """Inserts the last call popped into the front of the queue."""
        if self.last_call is None:
            return
        self.cond.acquire()
        self.queue.appendleft(self.last_call)
        self.cond.notify()
        self.cond.release()

    def consume(self) -> Ret | ratelimiting.TooManyReq | KillThread:
        """Consumes an element from the API queue (blocking)."""
        self.cond.acquire()
        while not self.queue:
            self.cond.wait()

        ret = self.queue.popleft()
        # Special Signals
        if isinstance(ret, (KillThread, ratelimiting.TooManyReq)):
            return ret

        # Process call and store its result
        call_result = self.__getattribute__(ret.service_method.__name__)(
            *ret.service_args
        )
        self.cond.release()
        return Ret(ret.cb_obj, ret.cb, ret.cb_args, call_result)

    def sleep(self, sleep_time: int) -> None:
        """Display warning trigger rate_limit callback, and sleep."""
        message = f'Hit rate limit, sleeping for {sleep_time}s'
        logger.warning(message)
        self.rate_limit(message)
        time.sleep(sleep_time)

    def run(self) -> None:
        """Runs the thread."""
        while True:
            # Block and wait if there is a rate limiter
            if self.rate_limiter is not None:
                sleep_time = self.rate_limiter.get_sleep_time()
                if sleep_time is not None:
                    self.sleep(sleep_time)
                    continue

            # Consume queue element (blocking if empty)
            ret = self.consume()

            # Add timestamp if there is a rate limiter
            if self.rate_limiter is not None:
                self.rate_limiter.insert()

            if isinstance(ret, KillThread):
                # Signal to exit the thread
                break

            if isinstance(ret, ratelimiting.TooManyReq):
                if self.rate_limiter is None:
                    logger.error('Service received too many requests, exiting')
                    break

                self.rate_limiter.update_rate_limits(ret.rate_limits)
                self.retry_last()
                self.sleep(ret.retry_after)
                continue

            self.service_success(ret)
        logger.info('Thread finished')

    @abc.abstractmethod
    def service_success(self, ret: Ret) -> None:
        """Callback for a successful service."""

    @abc.abstractmethod
    def rate_limit(self, message: Ret) -> None:
        """Callback for hitting rate limit."""
