"""
Prometheus metrics for DevOps Info Service
Implements RED method: Rate, Errors, Duration
"""
from prometheus_client import Counter, Histogram, Gauge

# Request counter - tracks total requests by method, endpoint, and status
# Used for: Request rate, error rate, status code distribution
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# Request duration histogram - tracks latency distribution
# Used for: P50, P95, P99 latency calculations
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

# Active requests gauge - tracks concurrent requests
# Used for: Current load monitoring
ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Active HTTP requests',
    ['method', 'endpoint']
)

# Application info gauge - tracks application version
APP_INFO = Gauge(
    'app_info',
    'Application information',
    ['version', 'python_version']
)

# Set application info on module load
import platform
APP_INFO.labels(version='1.0.0', python_version=platform.python_version()).set(1)
