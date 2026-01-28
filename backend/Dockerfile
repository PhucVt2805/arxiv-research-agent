FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY backend/pyproject.toml ./backend/
RUN uv sync --frozen --package arxiv-daily-digest-backend --no-dev

COPY backend/src ./backend/src

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app/backend

CMD ["python", "-m", "src.main"]