# Product Content Creation and Review Workbench

[简体中文](README.md) | **English**

A local, single-user portfolio project for apparel product-detail copy. **Only M1, the product-facts foundation, is currently implemented.** There has been no real customer validation; this is not a commercial system or a completed AI content workflow.

## Install and run

Requires Python 3.11, uv, and Git. The currently validated platform is macOS arm64.
Run from the project root:

```sh
uv sync --locked --python python3.11
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. Press Ctrl+C in the terminal to stop the service; product data persists across restarts.
The default database, `workbench.db`, lives in the project root and is excluded from Git. Tables are not created automatically; run migrations first.
Override the default path with the `WORKBENCH_DATABASE_URL` shell environment variable. M1 does not load `.env` automatically and needs no model key. Do not bind to `0.0.0.0`; there is no multi-user authentication.

Dependencies are declared in `pyproject.toml` and locked in `uv.lock`. Python is currently restricted to the 3.11 series to keep the initial validation matrix small.

## Tests and checks

```sh
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run alembic check
```

After `.venv` has been created, you can also invoke its tools directly, for example `.venv/bin/python -m pytest -q` or `.venv/bin/ruff check .`. This does not change how dependencies are managed.

For an actual HTTP smoke test, start the service above first, then run:

```sh
uv run python scripts/smoke_http.py
```

Each smoke test adds a synthetic product with a `DEMO-M1-` prefix to the local database and makes no model calls. Unit and integration tests use temporary databases, leaving the working database unchanged. Migration downgrades in tests affect only temporary databases; do not downgrade a database containing useful data.

## Implemented features

- Required style number and product name; optional color, size, confirmed material, and selling points.
- Text-length validation and case-sensitive unique style numbers; form input is preserved on errors.
- Product list, entry, and detail pages; unknown information is labeled as unconfirmed.
- SQLite persistence, minimal task/draft-version structures, and database constraints.
- Template escaping, form CSRF validation, localhost Host restrictions, and basic security response headers.

## Known limitations

- No generation calls, task executor, task recovery after restart, fact-conflict checks, review, editing, or export. These belong to M2–M4; M1 is not a complete workflow.
- Products can only be added and viewed, not edited or deleted. The list is not paginated and is intended for small learning samples.
- Passing text-format validation does not establish factual accuracy. M1 only stores facts asserted by the user.
- A task marked `running` does not automatically become successful. Execution and interruption recovery belong to M2; M1 pages do not create tasks.
- The Starlette test client reports two upstream deprecation warnings related to the httpx interface and the AnyIO BlockingPortal alias. The locked dependency combination passes existing tests; warnings are not hidden and should be rechecked during dependency updates.
- HTTP behavior and template output have been verified. Multi-browser, screen-reader, and complete visual/keyboard acceptance checks are not complete.
- Data is stored in a local plaintext SQLite database. There is no authentication, multi-tenancy, or production operations support. Use only in the intended local, single-user setting.

## Further reading

The following project documents are currently in Chinese:

- [Product boundaries](docs/PRODUCT_CONTRACT.md)
- [Development constraints](AGENTS.md)
- [Milestone plan](docs/IMPLEMENTATION_PLAN.md)
