"""CLI entrypoint: ``python -m app.seed``.

Wraps ``run_seed()`` in ``asyncio.run`` so the orchestrator can be called
both from the command line (in the running ``pulse-backend`` container) and
from test fixtures (which call ``run_seed`` directly without ``asyncio.run``
because pytest-asyncio already owns the loop).

The matching ``pulse-seed`` console script is declared in
``backend/pyproject.toml`` so ``pulse-seed`` and ``python -m app.seed`` both
work post-install.
"""

from __future__ import annotations

import asyncio

from app.seed import run_seed


def main() -> None:
    asyncio.run(run_seed())


if __name__ == "__main__":
    main()
