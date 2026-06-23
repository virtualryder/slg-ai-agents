FROM --platform=linux/arm64 python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app:/app/platform_core
COPY platform_core /app/platform_core
COPY governance /app/governance
RUN pip install --no-cache-dir -e /app/platform_core
COPY aws-native-reference/_shared/runtime/serve.py /app/serve.py
EXPOSE 8080
CMD ["python", "/app/serve.py"]
