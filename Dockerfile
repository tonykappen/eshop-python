FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy project files
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --no-interaction
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and start app
CMD ["poetry", "run", "uvicorn", "eshop.main:app", "--host", "0.0.0.0", "--port", "8000"] 