FROM node:22-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ ./backend/
COPY pipeline/ ./pipeline/
COPY fonts/ ./fonts/
COPY --from=frontend /build/frontend/dist ./frontend/dist
CMD ["sh", "-c", "exec .venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --no-access-log"]
