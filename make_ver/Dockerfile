FROM astral/uv:alpine AS base
    ENV UV_PROJECT_ENVIRONMENT=/.uv.venv
    ENV UV_NO_SYNC=True
    WORKDIR /make_ver/
FROM base AS dependencies
    COPY pyproject.toml uv.lock ./
    RUN UV_NO_SYNC=False uv sync --no-dev
FROM dependencies AS test_dependencies
    RUN UV_NO_SYNC=False uv sync

FROM dependencies AS code
    COPY . .

FROM test_dependencies AS test
    COPY --from=code /make_ver/ .
    CMD [ "uv", "run", "pytest" ]
FROM code AS production
    CMD [ "uv", "run", "api" ]
