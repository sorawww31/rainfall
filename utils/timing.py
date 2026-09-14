import math
import os
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
import logging
import psutil


@contextmanager
def trace(title: str, LOGGER: logging.Logger) -> Generator[None, None, None]:
    """
    Examples:
        >>> with trace("wait", LOGGER):
                time.sleep(2.0)
    """
    t0 = time.time()
    p = psutil.Process(os.getpid())
    m0 = p.memory_info().rss / 2.0**30
    yield
    m1 = p.memory_info().rss / 2.0**30
    delta = m1 - m0
    sign = "+" if delta >= 0 else "-"
    delta = math.fabs(delta)
    LOGGER.info(
        f"[{m1:.1f}GB({sign}{delta:.1f}GB):{time.time() - t0:.1f}sec] {title} "
    )


@contextmanager
def timer(name: str, LOGGER: logging.Logger) -> Generator[None, None, None]:
    """
    Examples:
        >>> with timer("wait", LOGGER):
                time.sleep(2.0)
    """
    t0 = time.time()
    yield
    elapsed_time = time.time() - t0
    LOGGER.info(f"[{name}] done in {elapsed_time:.1f} s")