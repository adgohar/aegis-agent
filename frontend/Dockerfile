FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc git \
 && rm -rf /var/lib/apt/lists/*

# Copy only requirements and smolagents FIRST
COPY requirements.txt ./
COPY smolagents/ ./smolagents

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the frontend
COPY . .

CMD ["streamlit", "run", "app.py", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false", \
     "--server.port=8501", \
     "--server.address=0.0.0.0"]
