# LAB02 — Docker Containerization

## 1. Docker Best Practices Applied

### 1.1 Non-root User
Running containers as root is insecure.  
I created a dedicated non-root user:

```dockerfile
RUN useradd -m appuser
USER appuser
```

This reduces the attack surface and follows Docker security best practices.

---

### 1.2 Slim Base Image
I selected:

```
python:3.13-slim
```

Reasons:
- Smaller size → faster builds and pulls  
- Fewer OS packages → reduced attack surface  
- Official Python image → maintained and secure  

---

### 1.3 Layer Caching
I copied `requirements.txt` before the application code:

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

This allows Docker to reuse cached layers when only the code changes, significantly speeding up rebuilds.

---

### 1.4 .dockerignore
I created a `.dockerignore` file to reduce build context:

```
__pycache__/
*.pyc
venv/
.git
docs/
tests/
```

This improves build speed and prevents unnecessary files from being included in the image.

---

### 1.5 Minimal Dependencies
Using:

```dockerfile
pip install --no-cache-dir
```

prevents pip from storing cached wheels, reducing final image size.

---

## 2. Image Information & Decisions

### Base Image
`python:3.13-slim` — modern, lightweight, secure.

### Final Image Size
~160 MB (depends on psutil).

### Layer Structure
1. Base image  
2. System dependencies  
3. Python dependencies  
4. Application code  
5. Non-root user  

### Optimization Choices
- Slim base image  
- No pip cache  
- Minimal apt packages  
- .dockerignore to reduce context  

---

## 3. Build & Run Process

### Build
```bash
docker build -t hiksol/devops-info-service:lab02 .
```

### Run
```bash
docker run -p 5000:5000 hiksol/devops-info-service:lab02
```

### Test
```bash
curl http://localhost:5000/
curl http://localhost:5000/health
```

### Docker Hub Repository
```
https://hub.docker.com/r/hiksol/devops-info-service
```

---

## 4. Technical Analysis

### Why this Dockerfile works well
- Slim image → small and secure  
- Layer caching → fast rebuilds  
- Non-root user → security best practice  
- Minimal COPY → efficient caching  

### What happens if layer order changes?
If I copy all files before installing dependencies:
- Docker will reinstall dependencies on every code change  
- Build time increases dramatically  

### Security Considerations
- Non-root user  
- Minimal OS packages  
- No cache  
- Slim base image  

### How .dockerignore helps
- Reduces build context  
- Speeds up builds  
- Prevents leaking secrets or unnecessary files  

---

## 5. Challenges & Solutions

### Challenge 1: Docker push failed due to uppercase username
Docker Hub usernames must be lowercase.

**Solution:**  
Retagged image:

```bash
docker tag Hiksol/... hiksol/...
```

### Challenge 2: Understanding layer caching
Initially unclear why requirements must be copied separately.

**Solution:**  
Learned that Docker caches layers and avoids reinstalling dependencies.