FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY frontend/pyproject.toml ./frontend/
RUN uv sync --frozen --package arxiv-daily-digest-frontend --no-dev

COPY frontend/src ./frontend/src

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app/frontend

CMD ["streamlit", "run", "src/main.py", "--server.address=0.0.0.0", "--server.port=8501"]