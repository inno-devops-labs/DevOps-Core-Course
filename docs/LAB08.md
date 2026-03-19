
# LAB 08


### General Information

**Objective:** To learn the basics of application monitoring using Prometheus and Grafana, and to implement metric collection and visualization  
**Date:** 19.03.2026
**Author:** Daniil Mayorov
**Email:** d.mayorov@innopolis.university   


---

### Architecture

Application metrics flow:
```
    app.py --> /metrics --> [Prometheus Scraper] --> [TSDB]
                                    |
                                    v
                             [Grafana Dashboard]
```
- App exposes metrics at /metrics
- Prometheus scrapes metrics every 15s
- Grafana visualizes metrics via Prometheus datasource

---

### Application Instrumentation
The following metrics have been added to the application:

1. Counter (http_requests_total)
   Used to count the total number of HTTP requests.
   Labels:
   - **method:** HTTP method (GET, POST)
   - **endpoint:** request endpoint
   - **status:** HTTP status code

2. Histogram (http_request_duration_seconds)
   Used to measure request execution time.

3. Gauge (http_requests_in_progress)
   Tracks the number of requests currently being processed.

The `/metrics` endpoint has been added to the application, which provides metrics in Prometheus format.
Prometheus uses this endpoint to collect data.

These metrics were chosen based on the RED method:

- Rate (requests per second) → implemented using http_requests_total
- Errors (error rate) → derived from http_requests_total with status codes
- Duration (latency) → implemented using http_request_duration_seconds

This approach provides a complete overview of application performance.

![change1](./screenshots/change1.png)

The `before_request` and `after_request` hooks were used to automatically collect metrics.

Before the request is processed:
- The `Gauge` value (active requests) is incremented
- The request start time is recorded

After processing:
- The request counter (`Counter`) is incremented
- The request duration is recorded (`Histogram`)
- The `Gauge` value is decremented

![change2](./screenshots/change2.png)

---

### Prometheus Configuration
Prometheus was deployed using Docker Compose.

Key configuration:
- **Image:** `prom/prometheus:v3.9.0`
- **Port:** `9090`
- **Configuration file** mounted to `/etc/prometheus/prometheus.yml`
- **Persistent storage** configured using a Docker volume (prometheus-data)
Prometheus is connected to the same network as Grafana and Loki.

Prometheus was configured with multiple scrape targets:
- **prometheus:** self-monitoring (localhost:9090)
- **app:** Python application (host.docker.internal:5000/metrics)
- **loki:** log aggregation service (loki:3100)
- **grafana:** visualization service (grafana:3000)

Scrape interval was set to 15 seconds.

```yml
prometheus:
    image: prom/prometheus:v3.9.0
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    networks:
      - logging
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

### Dashboard Walkthrough

- Grafana Prometheus data source connected to http://prometheus:9090
- Allows querying application metrics and creating panels

![task3result1](./screenshots/task3-result1.png)

---

### PromQL Examples

`http_requests_total`: 
![grf1](./screenshots/grf1.png)

`http_requests_total{method="GET"}`:
![grf2](./screenshots/grf2.png)

`http_requests_total{endpoint="/",status="200"}`:
![grf3](./screenshots/grf3.png)

`sum(rate(http_requests_total[5m])) by (endpoint)`:
![grf4](./screenshots/grf4.png)

`sum(rate(http_requests_total{status=~"5.."}[5m]))`:
![grf5](./screenshots/grf5.png)

`up{job="app"}`:
![grf6](./screenshots/grf6.png)

`rate(http_requests_in_progress[5m])`:
![grf7](./screenshots/grf7.png)

Complete Dashboard:
![cmpplgrf](./screenshots/grfcommon8.png)


---

### Production Setup
#### Health Checks - each service checks its own status:
- **App:** /health
- **Prometheus:** /-/healthy
- **Grafana:** /api/health
- **Loki:** /ready

#### Resource Limits – CPU and memory limits for stability:
- **App, Prometheus, Grafana, Loki, Promtail:** CPU 1.0 / 0.5, RAM 1G / 512M
- **Data Retention & Persistence:** metrics and logs are retained:
- **Prometheus:** 15 days / 10GB
- **Grafana and Loki via volumes:** grafana-data, loki-data, prometheus-data

#### Data persists after container restarts
- **Benefits**: automatic health monitoring, resource control, data persistence.


---

### Testing Results

#### Metrics were tested locally using the `/metrics` endpoint.

Steps:
1. The application was started
2. Requests were sent to `/` and `/health`
3. Metrics were accessed via `/metrics`

Example output:

http_requests_total{method="GET",endpoint="/",status="200"} 1.0

This confirms that:
- Requests are being counted correctly
- Request duration is being measured
- Active requests are tracked

Example of run:
![exmpofrun3](./screenshots/runexample3.png)
![exmpofrun3-2](./screenshots/runexample3-2.png)

#### Prometheus
Prometheus was successfully deployed and verified.

Steps:
1. Docker Compose stack was started
2. Prometheus UI was accessed at http://localhost:9090
3. Targets page was checked

All targets were in "UP" state, confirming successful metric scraping.

The following targets were monitored:
- Prometheus
- Application
- Loki
- Grafana

A test query `up` was executed in Prometheus UI, showing all services as available.
![check4](./screenshots/check4.png)
![check5](./screenshots/check5.png)

---

### Challenges & Solutions

1) *TypeError: unsupported operand type(s) for 'float' and 'datetime.datetime'*

**Cause:**
The variable `request.start_time` was used simultaneously for logging (datetime) and metrics (float), which led to a type conflict.

**Solution:**
Different variables were used for logging and metrics:
- `request.start_time (float)` - for metrics
- `request.log_start_time (datetime)` - for logging

Additionally, the `after_request` functions were combined into a single function to improve code stability and readability.