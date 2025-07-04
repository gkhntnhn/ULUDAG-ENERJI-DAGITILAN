# Dockerfile

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# 1) Copy environment file for python-dotenv
COPY .env ./

# 2) Copy dependency files
COPY pyproject.toml uv.lock ./

# 3) Sync UV environment, export to requirements.txt, then install via pip
RUN uv sync --locked \
 && uv export --format requirements.txt --output-file requirements.txt \
 && pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# 4) Copy the rest of the application code
COPY . /app

# 5) Create runtime directories with restricted permissions
RUN mkdir -p input output send \
 && chmod 700 input output send

EXPOSE 80

# 6) Start the app with Gunicorn, extended timeout for long-running jobs
CMD ["gunicorn", "app:app", "--workers", "4", "--bind", "0.0.0.0:80", "--timeout", "6000"]
