"""Structlog configuration shared across the FastAPI app and CLI scripts.

`configure_logging()` is idempotent and safe to call from app lifespan,
test fixtures, or worker entrypoints. Logs render as a developer-friendly
console stream when `APP_ENV=local`, and JSON otherwise (Docker, CI, prod).
"""

from __future__ import annotations

import logging
import sys

import structlog
from structlog.types import Processor

from app.core.config import settings


def _shared_processors() -> list[Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]


def configure_logging() -> None:
    is_local = settings.APP_ENV == "local"
    final_processor: Processor = (
        structlog.dev.ConsoleRenderer(colors=is_local and sys.stderr.isatty())
        if is_local
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[
            *_shared_processors(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping().get(settings.LOG_LEVEL.upper(), logging.INFO)
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_shared_processors(),
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            final_processor,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.LOG_LEVEL.upper())

    # Quiet down noisy third-party loggers; keep at INFO when explicitly set lower.
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
