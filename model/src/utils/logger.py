"""
model.src.utils.logger
~~~~~~~~~~~~~~~~~~~~~~~
Centralised logging configuration for the ML pipeline.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path


def get_logger(name: str, log_file: Path | None = None, level: int = logging.INFO) -> logging.Logger:
    """
    Return a configured logger.

    Args:
        name:     Logger name (usually ``__name__`` of the calling module).
        log_file: Optional file path to also write logs to.
        level:    Logging level (default INFO).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:  # already configured — return as-is
        return logger

    logger.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # Optional file handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
