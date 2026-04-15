# Fixed version of Python, slim variant (lightweight, smaller attack surface)
FROM python:3.13-slim

# Containerized Python behavior settings (no __pycache__/*.pyc, unbuffered output)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create an unprivileged user (safer, less attacker power)
RUN useradd --create-home --uid 1001 --shell /usr/sbin/nologin appuser

# All further actions will be performed from the /app directory.
WORKDIR /app

# Copying the requirements.txt file into the container, installing the dependencies described in it, and deleting the cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copying the app.py executable into the container
COPY app.py .

# Create application data directory for persistent files
RUN mkdir -p /data

# Granting ownership rights to the /app directory and all files in it to the user appuser
RUN chown -R appuser:appuser /app /data
USER appuser

# Defining the container port on which the application will run
EXPOSE 5000

# Define startup command
CMD ["python", "app.py"]