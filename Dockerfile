# Dockerfile
FROM python:3.13-slim

# Install basic system deps (optional but usually helpful)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1) Copy dependency file(s) first for caching
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 2) Copy the actual app code
COPY main.py .

# Expose port (for documentation; docker-compose does the mapping)
EXPOSE 8000

# Start FastAPI app (assuming main.py with app = FastAPI())
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
