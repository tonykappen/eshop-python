FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir poetry

# Configure poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Copy poetry files first for better caching
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --only=main --no-interaction

# Copy the entire backend directory
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and start app
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
