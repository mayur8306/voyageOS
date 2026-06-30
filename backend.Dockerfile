FROM python:3.11-slim
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p downloads && chmod -R 777 downloads
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]