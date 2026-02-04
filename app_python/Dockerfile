    FROM python:3.13-slim

    # Env vars 
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1
    
    # Create non-root user 
    RUN useradd -m -u 10001 appuser
    
    # set working directory 
    WORKDIR /app
    
    # system dependencies 
    RUN apt-get update \
        && apt-get install -y --no-install-recommends curl \
        && rm -rf /var/lib/apt/lists/*
    
    # copy dependencies first (layer caching) 
    COPY requirements.txt .
    
    # Python dependencies 
    RUN pip install --no-cache-dir -r requirements.txt
    
    # copy application code 
    COPY app.py .
    
    # switch to non-root user 
    USER appuser
    
    # expose application port 
    EXPOSE 5000
    
    # start application 
    CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
    