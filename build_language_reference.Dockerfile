FROM astral/uv:python3.14-alpine AS base
ENV UV_PROJECT_ENVIRONMENT=/.uv.venv
ENV UV_NO_SYNC=True
WORKDIR /app/
RUN uv venv && uv pip install falcon
COPY . .
RUN uv run api.py --path_language language_reference/languages/ --path_export .
