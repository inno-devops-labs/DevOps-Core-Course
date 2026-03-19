"""Prometheus metrics definitions."""

from prometheus_client import Counter, Histogram, Gauge

# HTTP metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed'
)

# Application-specific metrics
devops_info_endpoint_calls = Counter(
    'devops_info_endpoint_calls', 
    'DevOps info endpoint calls', 
    ['endpoint']
)

system_info_collection_duration = Histogram(
    'devops_info_system_collection_seconds', 
    'System info collection time'
)