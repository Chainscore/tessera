# Dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    librocksdb-dev \
    iputils-ping \
    procps \
    net-tools \
    python3-dev \
    pkg-config \
    libffi-dev \
    libssl-dev \
    cmake \
    rustc \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Install pip, wheel tooling and install build-time Python packages
RUN python3 -m pip install --upgrade pip setuptools wheel \
 && python3 -m pip install --no-cache-dir mypy librt maturin

# Install uv via shell installer
RUN curl -sSL https://astral.sh/uv/install.sh | sh -s --  \
  && echo "uv installed to:" && which uv || true

ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy the entire application
COPY . .

# setup
RUN chmod +x /app/scripts/setup.sh

# Initialize git submodules (assuming private token is available via build args)
ARG GITHUB_TOKEN
RUN if [ -n "$GITHUB_TOKEN" ]; then \
        git config --global url."https://x-access-token:${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/" && \
        git submodule update --init deps/py-ark-vrf deps/tsrkit-pvm deps/tsrkit-asm deps/rockstore deps/tsrkit-types; \
    else \
        echo "Warning: GITHUB_TOKEN not provided, skipping submodule init"; \
    fi


# Run the application
# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
