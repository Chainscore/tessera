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
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
# Ensure Poetry is on PATH
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy the entire application
COPY . .

# Initialize git submodules (assuming private token is available via build args)
ARG GITHUB_TOKEN
RUN if [ -n "$GITHUB_TOKEN" ]; then \
        git config --global url."https://x-access-token:${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/" && \
        git submodule update --init deps/py-ark-vrf deps/tsrkit-pvm deps/tsrkit-asm; \
    else \
        echo "Warning: GITHUB_TOKEN not provided, skipping submodule init"; \
    fi

# Configure Poetry to NOT use virtualenvs
RUN poetry config virtualenvs.create false

# Install all dependencies and the project itself
RUN poetry install --only=main --no-interaction --no-ansi

# Create data directory with permissions
RUN mkdir -p data/db && chmod -R 777 data

# Expose application port
EXPOSE 8000

# Run the FastAPI application
CMD ["poetry", "run", "fastapi", "run", "jam/api/api-service.py", "--host", "0.0.0.0", "--port", "8000"]
