from prometheus_client import Counter, Histogram, Gauge

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)

endpoint_calls = Counter(
    "devops_info_endpoint_calls",
    "Endpoint calls by endpoint name",
    ["endpoint"],
)

system_info_duration = Histogram(
    "devops_info_system_collection_seconds",
    "Time to collect system info",
)
