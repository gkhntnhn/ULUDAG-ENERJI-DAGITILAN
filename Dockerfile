# 1) Base imaj: uv aracı ve Python 3.12 önceden kurulmuş
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# 2) Çalışma dizini
WORKDIR /app

# 3) Salt bağımlılık tanımları
COPY pyproject.toml uv.lock ./

# 4) Bağımlılıkları tek RUN içinde kur
RUN uv sync --locked && \
    uv export --format requirements.txt --output-file requirements.txt && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5) Uygulama kodunu kopyala
COPY . .

# 6) Port ve çalıştırma
EXPOSE 80
CMD ["gunicorn", "app:app", "--workers", "4", "--bind", "0.0.0.0:80", "--timeout", "3600"]
