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

# Configure Poetry to NOT use virtualenvs
RUN poetry config virtualenvs.create false

# Install all dependencies and the project itself
RUN poetry install --no-interaction --no-ansi $(poetry --version | grep -q "Poetry (version 1.[0-1]" && echo "--no-dev" || echo "--without dev")

# Run the application
# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
#ENTRYPOINT ["poetry", "run", "jam"]

# Create data directory with permissions
#RUN mkdir -p data/db && chmod -R 777 data

# Expose application port
#EXPOSE 8000

# Run the FastAPI application
#CMD ["poetry", "run" ,"fastapi", "run", "jam/api/api-service.py", "--host", "0.0.0.0", "--port", "8000"]
