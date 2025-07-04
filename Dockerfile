# 1. uv imajından başla
FROM ghcr.io/astral-sh/uv:python3.12-slim-bookworm

# 2. uv için sistem ortamı
ENV UV_PROJECT_ENVIRONMENT=system

# 3. Çalışma dizini
WORKDIR /app

# 4. Bağımlılıkları yükle
COPY pyproject.toml uv.lock* ./
RUN uv sync --locked

# 5. Uygulama kodunu kopyala
COPY . /app

# 6. Klasörleri oluştur ve izinleri kıs
RUN mkdir -p input output send \
    && chmod 700 input output send

# 7. Port aç
EXPOSE 80

# 8. Production’da gunicorn ile başlat
CMD ["gunicorn", "app:app", "--workers", "4", "--bind", "0.0.0.0:80"]