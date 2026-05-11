"""Structured JSON logging for the PULSE backend.

Emits to stdout via stdlib `logging.basicConfig` so Docker / gunicorn log
collectors see one JSON record per line. No plaintext payload bodies, no
secrets (Pydantic `SecretStr` redacts on repr).

Silences the cosmetic `passlib.handlers.bcrypt` 1.7.4 warning at startup
(RESEARCH.md Pitfall 3) so the JSON log stream stays clean.
"""

import logging
import sys

import structlog


def configure_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)
    # Silence the cosmetic passlib/bcrypt 1.7.4 warning per RESEARCH Pitfall 3
    logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.ERROR)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "pulse"):
    return structlog.get_logger(name)
