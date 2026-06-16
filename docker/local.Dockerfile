FROM python:3.13.3-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1\
    PYTHONUNBUFFERED=1 \
    UV_NO_DEV=1 \
    UV_SYSTEM_PYTHON=1\
    UV_COMPILE_BYTECODE=1\
    UV_TOOL_BIN_DIR=/usr/local/bin

WORKDIR /app

RUN apt-get update && apt-get install -y \
    # LDAP dependencies
    libldap2-dev \
    libsasl2-dev \
    ldap-utils \
    # MSSQL dependencies
    curl \
    gnupg2 \
    # PostgreSQL dependencies
    libpq-dev \
    # Build tools
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Microsoft repo + ODBC driver/tools (Debian 12 / bookworm)
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl gnupg2; \
    curl -sSL -O https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb; \
    dpkg -i packages-microsoft-prod.deb; \
    rm -f packages-microsoft-prod.deb; \
    apt-get update; \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
    msodbcsql18 \
    mssql-tools18 \
    unixodbc-dev \
    libgssapi-krb5-2; \
    rm -rf /var/lib/apt/lists/*


COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

EXPOSE 8000

CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8000"]


