import json

panels = []
def add_panel(id, title, ptype, gridPos, targets, options=None):
    p = {
        "id": id,
        "title": title,
        "type": ptype,
        "gridPos": gridPos,
        "datasource": {"type": "prometheus", "uid": "Prometheus"},
        "targets": [{"expr": e, "refId": chr(65+i)} for i, e in enumerate(targets)]
    }
    if options:
        p.update(options)
    panels.append(p)

add_panel(1, "Request Rate", "timeseries", {"h": 8, "w": 12, "x": 0, "y": 0}, ["sum(rate(http_requests_total[5m])) by (endpoint)"])
add_panel(2, "Error Rate", "timeseries", {"h": 8, "w": 12, "x": 12, "y": 0}, ["sum(rate(http_requests_total{status=~'5..'}[5m]))"])
add_panel(3, "Request Duration p95", "timeseries", {"h": 8, "w": 12, "x": 0, "y": 8}, ["histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))"])
add_panel(4, "Request Duration Heatmap", "heatmap", {"h": 8, "w": 12, "x": 12, "y": 8}, ["sum(rate(http_request_duration_seconds_bucket[5m])) by (le)"], {"options": {"calculate": False}, "color": {"mode": "scheme"}})
add_panel(5, "Active Requests", "stat", {"h": 8, "w": 8, "x": 0, "y": 16}, ["http_requests_in_progress"])
add_panel(6, "Status Code Distribution", "piechart", {"h": 8, "w": 8, "x": 8, "y": 16}, ["sum by (status) (rate(http_requests_total[5m]))"])
add_panel(7, "Uptime", "stat", {"h": 8, "w": 8, "x": 16, "y": 16}, ["up{job='app'}"])

dashboard = {
    "title": "App Metrics",
    "uid": "app_metrics",
    "schemaVersion": 39,
    "panels": panels,
    "timezone": "browser",
    "refresh": "5s",
    "time": {"from": "now-1h", "to": "now"}
}

with open(r"c:\Projects\DevOps\DevOps-Core-Course\monitoring\grafana\dashboards\app_metrics.json", "w") as f:
    json.dump(dashboard, f, indent=2)
