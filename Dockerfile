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
    rustc \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Install uv via shell installer
RUN curl -sSL https://astral.sh/uv/install.sh | sh -s --  \
  && echo "uv installed to:" && which uv || true

ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy the entire application
COPY . .

# Build PVM cython
RUN if [ -d deps/tsrkit-pvm ]; then \
        cd deps/tsrkit-pvm && \
        echo "[INFO] Building tsrkit-pvm with Cython optimizations..." && \
        # careful with -march=native (non-portable); remove if portability needed
        PVM_BUILD_MODE=cython /root/.local/bin/uv run python setup.py build_ext --inplace --force; \
        cd /app; \
    else \
        echo "[WARN] deps/tsrkit-pvm not found, skipping tsrkit-pvm build"; \
    fi

RUN uv sync

# Run the application
# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
