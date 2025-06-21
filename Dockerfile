###############################################################################
#  Dockerfile — ФинАтлас (prod, SQLite-based)                                #
#  • multi-stage: wheels → slim runtime                                       #
#  • non-root user, pinned system libs, SQLite db on volume ­/app/…           #
###############################################################################

# ─────────────── builder ────────────────────────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /build

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# ─────────────── runtime ────────────────────────────────────────────────────
FROM python:3.12-slim

### 1. базовые переменные окружения
RUN set -eux; \
    # скачиваем пакеты для работы Selenium (chromedriver для linux)
    # 1) базовые инструменты для скачивания ключа
    apt-get update && apt-get install -y --no-install-recommends \
        wget ca-certificates gnupg; \
    # 2) подключаем репозиторий Google Chrome
    mkdir -p /etc/apt/keyrings; \
    wget -qO- https://dl.google.com/linux/linux_signing_key.pub \
      | gpg --dearmor -o /etc/apt/keyrings/google.gpg; \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google.gpg] \
         http://dl.google.com/linux/chrome/deb/ stable main" \
         > /etc/apt/sources.list.d/google.list; \
    # 3) ставим Chrome + все GUI deps _без_ =version
    apt-get update && \
    apt-get install -y --no-install-recommends \
        google-chrome-stable \
        libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 \
        libgtk-3-0 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxdamage1 \
        libxrandr2 libxss1 libxi6 libxtst6 libatk1.0-0 libgdk-pixbuf2.0-0 \
        libpangocairo-1.0-0 libasound2 libcups2 fonts-liberation xdg-utils lsb-release; \
    # 4) «замораживаем» установленные версии, чтобы они не менялись внезапно
    apt-mark hold google-chrome-stable libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1; \
    # 5) чистим кеш
    rm -rf /var/lib/apt/lists/*

### 2. системные зависимости (pinned версии)
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        libglib2.0-0=2.74.6-2+deb12u6 \
        libnss3=2:3.87.1-1+deb12u1 \
        libgconf-2-4=3.2.6-8 \
        libfontconfig1=2.14.1-4 \
    ; \
    apt-mark hold libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1; \
    rm -rf /var/lib/apt/lists/*

### 3. Python-зависимости — колёса из builder
COPY --from=builder /wheels /wheels
# COPY docker-compose.yml /app/docker-compose.yml
RUN pip install --no-cache-dir /wheels/*

### 4. непривилегированный пользователь и рабочая директория
RUN adduser --disabled-password --gecos '' finatlas
USER finatlas
WORKDIR /app

### 5. приложение
COPY --chown=finatlas . .

### 6. порт + команда запуска
# Переменные окружения для Flask
ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=10000

EXPOSE $PORT

CMD ["sh", "-c", "gunicorn -k gevent --worker-connections 1000 -w 1 -t 0 -b 0.0.0.0:$PORT app:app"]
# CMD ["sh","-c","gunicorn app:app -b 0.0.0.0:$PORT"]

