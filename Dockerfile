FROM python:3.12-slim
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app_code
RUN mkdir -p /app_code/data /app_code/app/static/uploads
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# RUN chown -R someuser:somegroup /app_code/data /app_code/app/static/uploads
# RUN chmod -R 755 /app_code/data /app_code/app/static/uploads

EXPOSE 8000
VOLUME /app_code/data
VOLUME /app_code/app/static/uploads

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
