# Docker Implementation Details

## Best Practices Applied

### 1. Multi-stage Build
- **Builder pattern** reduces final image size
- Separates build dependencies from runtime

### 2. Non-root User
- Created dedicated `appuser` user
- `USER` directive before running application

### 3. Security
- `.dockerignore` prevents sensitive file exposure
- `--no-cache-dir` in pip install
- Explicit package versions in requirements.txt

### 4. Layer Optimization
- Ordered COPY commands by change frequency
- Cached requirements installation layer

### 5. Image Efficiency
- Cleaned build artifacts between stages

### 6. Reproducibility
- Pinned base image version (`python:3.12-alpine`)
- Explicit port declaration (`EXPOSE 5000`)
