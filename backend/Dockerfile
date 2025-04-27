FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1) Install system packages
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
      g++ \
      libffi-dev \
      libopenblas-dev \
      liblapack-dev \
 && rm -rf /var/lib/apt/lists/*

# 2) Copy only the backend requirements and install deps
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 3) Copy the rest of your backend code
COPY . .

# 4) Launch Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
