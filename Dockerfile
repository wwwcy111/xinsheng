FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# 构建上下文为仓库根目录，依赖文件位于 backend/ 下
COPY backend/requirements.txt .

RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple \
    && pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/run.py .

RUN mkdir -p uploads app/static/cache

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]