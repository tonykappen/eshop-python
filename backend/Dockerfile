FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    pkg-config \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir poetry

# Configure poetry to not create virtual environment and use system packages
RUN poetry config virtualenvs.create false && \
    poetry config installer.max-workers 10

# Copy poetry files first for better caching
COPY pyproject.toml poetry.lock ./

# Install dependencies - update if requested or if lock file is stale
RUN poetry lock && poetry install --no-root --no-interaction --no-cache

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start the application (database initialization is handled by the Python code)
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
