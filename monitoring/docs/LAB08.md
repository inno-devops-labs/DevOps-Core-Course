# Lab 8 — Metrics & Monitoring with Prometheus

## Architecture

## Application Instrumentation



```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/monitoring$ curl http://localhost:8000/metrics
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 51230.0
python_gc_objects_collected_total{generation="1"} 4708.0
python_gc_objects_collected_total{generation="2"} 0.0
# HELP python_gc_objects_uncollectable_total Uncollectable objects found during GC
# TYPE python_gc_objects_uncollectable_total counter
python_gc_objects_uncollectable_total{generation="0"} 0.0
python_gc_objects_uncollectable_total{generation="1"} 0.0
python_gc_objects_uncollectable_total{generation="2"} 0.0
# HELP python_gc_collections_total Number of times this generation was collected
# TYPE python_gc_collections_total counter
python_gc_collections_total{generation="0"} 62.0
python_gc_collections_total{generation="1"} 5.0
python_gc_collections_total{generation="2"} 0.0
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="13",patchlevel="11",version="3.13.11"} 1.0
# HELP process_virtual_memory_bytes Virtual memory size in bytes.
# TYPE process_virtual_memory_bytes gauge
process_virtual_memory_bytes 1.66699008e+08
# HELP process_resident_memory_bytes Resident memory size in bytes.
# TYPE process_resident_memory_bytes gauge
process_resident_memory_bytes 5.490688e+07
# HELP process_start_time_seconds Start time of the process since unix epoch in seconds.
# TYPE process_start_time_seconds gauge
process_start_time_seconds 1.77325799615e+09
# HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 48.32
# HELP process_open_fds Number of open file descriptors.
# TYPE process_open_fds gauge
process_open_fds 15.0
# HELP process_max_fds Maximum number of open file descriptors.
# TYPE process_max_fds gauge
process_max_fds 1.048576e+06
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/metrics",method="GET",status_code="200"} 1379.0
http_requests_total{endpoint="/health",method="GET",status_code="200"} 675.0
# HELP http_requests_created Total HTTP requests
# TYPE http_requests_created gauge
http_requests_created{endpoint="/metrics",method="GET",status_code="200"} 1.7732580016874638e+09
http_requests_created{endpoint="/health",method="GET",status_code="200"} 1.7732580016886492e+09
# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.005",method="GET"} 1310.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.01",method="GET"} 1378.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.025",method="GET"} 1378.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.05",method="GET"} 1378.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.075",method="GET"} 1378.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.1",method="GET"} 1378.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.25",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.5",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.75",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="1.0",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="2.5",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="5.0",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="7.5",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="10.0",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="+Inf",method="GET"} 1379.0
http_request_duration_seconds_count{endpoint="/metrics",method="GET"} 1379.0
http_request_duration_seconds_sum{endpoint="/metrics",method="GET"} 3.339381251056693
http_request_duration_seconds_bucket{endpoint="/health",le="0.005",method="GET"} 669.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.01",method="GET"} 669.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.025",method="GET"} 669.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.05",method="GET"} 671.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.075",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.1",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.25",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.5",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.75",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="1.0",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="2.5",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="5.0",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="7.5",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="10.0",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="+Inf",method="GET"} 675.0
http_request_duration_seconds_count{endpoint="/health",method="GET"} 675.0
http_request_duration_seconds_sum{endpoint="/health",method="GET"} 0.5872745100277825
# HELP http_request_duration_seconds_created HTTP request duration in seconds
# TYPE http_request_duration_seconds_created gauge
http_request_duration_seconds_created{endpoint="/metrics",method="GET"} 1.7732580016875052e+09
http_request_duration_seconds_created{endpoint="/health",method="GET"} 1.7732580016886709e+09
# HELP http_requests_in_progress HTTP requests currently being processed
# TYPE http_requests_in_progress gauge
# HELP devops_info_endpoint_calls_total DevOps info service endpoint calls
# TYPE devops_info_endpoint_calls_total counter
# HELP devops_info_system_collection_seconds Time spent collecting system info (seconds)
# TYPE devops_info_system_collection_seconds histogram
devops_info_system_collection_seconds_bucket{le="0.005"} 0.0
devops_info_system_collection_seconds_bucket{le="0.01"} 0.0
devops_info_system_collection_seconds_bucket{le="0.025"} 0.0
devops_info_system_collection_seconds_bucket{le="0.05"} 0.0
devops_info_system_collection_seconds_bucket{le="0.075"} 0.0
devops_info_system_collection_seconds_bucket{le="0.1"} 0.0
devops_info_system_collection_seconds_bucket{le="0.25"} 0.0
devops_info_system_collection_seconds_bucket{le="0.5"} 0.0
devops_info_system_collection_seconds_bucket{le="0.75"} 0.0
devops_info_system_collection_seconds_bucket{le="1.0"} 0.0
devops_info_system_collection_seconds_bucket{le="2.5"} 0.0
devops_info_system_collection_seconds_bucket{le="5.0"} 0.0
devops_info_system_collection_seconds_bucket{le="7.5"} 0.0
devops_info_system_collection_seconds_bucket{le="10.0"} 0.0
devops_info_system_collection_seconds_bucket{le="+Inf"} 0.0
devops_info_system_collection_seconds_count 0.0
devops_info_system_collection_seconds_sum 0.0
# HELP devops_info_system_collection_seconds_created Time spent collecting system info (seconds)
# TYPE devops_info_system_collection_seconds_created gauge
devops_info_system_collection_seconds_created 1.773257998585445e+09
```

![](/monitoring/docs/screenshots/browser_metrics.png)

## Prometheus Configuration

![](/monitoring/docs/screenshots/prometheus_targets.png)

```yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "app"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["devops-info-service:5000"]

  - job_name: "loki"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["loki:3100"]

  - job_name: "grafana"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["grafana:3002"]
```

## Dashboard Walkthrough

![](/monitoring/docs/screenshots/dashboard_1.png)
![](/monitoring/docs/screenshots/dashboard_2.png)

## PromQL Examples

## Production Setup

## Testing Results

## Challenges & Solutions
