FROM grafana/promtail:3.0.0

# Add curl for healthcheck endpoints (base image lacks curl/wget/nc)
RUN sed -i '/bullseye-backports/d' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*
