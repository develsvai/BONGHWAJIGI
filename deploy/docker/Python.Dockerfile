FROM ghcr.io/astral-sh/uv:0.11.10 AS uv
FROM python:3.12-slim-bookworm AS runtime

COPY --from=uv /uv /bin/uv
WORKDIR /app
ARG RUNTIME_EXTRA=server
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations
COPY tools ./tools
RUN uv sync --frozen --no-dev --extra "$RUNTIME_EXTRA" \
    && useradd --create-home --uid 10001 app \
    && mkdir -p /models \
    && chown app:app /models
USER app
EXPOSE 8000
CMD ["uvicorn", "bonghwajigi.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
