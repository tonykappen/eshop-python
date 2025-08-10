FROM python:3.12

WORKDIR /app/

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY ./pyproject.toml ./poetry.lock* /app/

# Configure poetry: Don't create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev

# Copy app code
COPY ./app /app/app
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
