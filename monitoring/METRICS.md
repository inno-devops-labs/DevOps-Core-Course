# Metrics

## Task 1: Prometheus

check that `Prometheus` is working:

![image](https://github.com/user-attachments/assets/4b3cbe4d-38a5-45c9-85b0-5cd372118f2f)


## Task 2: Grafana Dashboards

### Dashboards

`Grafana` with `Prometheus` dashboard (imported from [here](https://grafana.com/grafana/dashboards/3662-prometheus-2-0-overview/))

![image](https://github.com/user-attachments/assets/b8f2c927-a028-4ee4-aeee-90a49860735d)

`Grafana` with `Loki` dashboard (imported from [here](https://grafana.com/grafana/dashboards/17781-loki-metrics-dashboard/))

![image](https://github.com/user-attachments/assets/527b9019-76ed-4b07-81e2-9163028af5b7)


### Log rotation mechanisms

```yaml
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Memory limits for containers

Now for all containers memory limit is `512M`.

```yaml
    deploy:
      resources:
        limits:
          memory: 512M
```

### Metrics Gathering

prometheus updated config:

```yml
global:
  scrape_interval: 30s
  evaluation_interval: 30s

scrape_configs:
  - job_name: "app_python"
    static_configs:
      - targets: ["app_python:8080"]

  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "loki"
    static_configs:
      - targets: ["loki:3100"]

  - job_name: "grafana"
    static_configs:
      - targets: ["grafana:3000"]

![image](https://github.com/user-attachments/assets/4b3cbe4d-38a5-45c9-85b0-5cd372118f2f)

  - job_name: "promtail"
    static_configs:
      - targets: ["promtail:9080"]
```

![image](https://github.com/user-attachments/assets/4b3cbe4d-38a5-45c9-85b0-5cd372118f2f)
