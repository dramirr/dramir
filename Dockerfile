FROM python:3.11-slim

WORKDIR /app

# نصب وابستگی‌های سیستم (gcc برای cryptography و بسته‌های دیگر)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# کپی کردن requirements.txt
COPY backend/requirements.txt .

# نصب Python packages
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن تمام فایل‌های پروژه
COPY . .

# ایجاد دایرکتوری‌های ضروری
RUN mkdir -p /data/uploads /data/backups /app/logs

# دسترسی اجرایی برای init.sh
RUN chmod +x init.sh

# تنظیم متغیرهای محیطی
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=backend/app.py
ENV PORT=5000
ENV HOST=0.0.0.0

# پورت مورد استفاده
EXPOSE 5000

# هلث‌چک (اختیاری اما توصیه‌شده)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:5000/health', timeout=5)" || exit 1

# اجرای برنامه
CMD ["bash", "init.sh"]