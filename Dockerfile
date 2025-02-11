# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    librocksdb-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
# Ensure Poetry is on PATH
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy only dependency files first to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install dependencies via Poetry (without dev deps)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy rest of the application
COPY . .

# Create data directory
RUN mkdir -p data/db

# Expose application port
EXPOSE 30333

# Run the application
CMD ["poetry", "run", "jam"]