# LAB08 — Metrics Choices (Short Notes)

## Why these metrics

I selected metrics based on the **RED method** for HTTP services:
- **Rate**: how many requests the service handles
- **Errors**: how many requests fail (by status code)
- **Duration**: how fast the service responds

## Implemented metrics

### 1) `http_requests_total` (Counter)
Tracks total HTTP requests.

**Labels:**
- `method` (GET, POST, ...)
- `endpoint` (`/`, `/health`, `/metrics`, ...)
- `status_code` (200, 404, 500, ...)

**Why:**
- Core traffic metric (Rate)
- Helps calculate error rates (4xx/5xx)

---

### 2) `http_request_duration_seconds` (Histogram)
Tracks request latency distribution.

**Labels:**
- `method`
- `endpoint`
- `status_code`

**Why:**
- Measures performance (Duration)
- Enables p95/p99 latency queries in Prometheus/Grafana

---

### 3) `http_requests_in_progress` (Gauge)
Tracks number of requests currently being processed.

**Labels:**
- `method`
- `endpoint`

**Why:**
- Shows current load/concurrency
- Useful for detecting overload spikes

---

### 4) `devops_info_endpoint_calls_total` (Counter)
App-specific metric for endpoint usage.

**Label:**
- `endpoint`

**Why:**
- Simple business-level usage visibility
- Helps compare endpoint popularity

---

### 5) `devops_info_system_collection_seconds` (Histogram)
Tracks time spent collecting system information.

**Why:**
- Measures internal operation cost
- Helps identify expensive code paths

## Notes on labels

Labels were chosen to keep **low cardinality** and still provide useful analysis.
No user-specific/dynamic IDs are used as labels.
