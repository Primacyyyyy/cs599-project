FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8888
# 启动 FastAPI 服务
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8888"]
