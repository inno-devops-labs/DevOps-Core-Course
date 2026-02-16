# Metrics lab

## Screenshots

- screenshot that confirm the successful setup

![targets](./screenshots/prmetheusTargets.png)

- Dashboards for Loki

![loki 1](./screenshots/lokiDashboard.png)


![loki 2](./screenshots/lokidashboard2.png)


- Dashboards for Prometheus 

![prometheus 1](./screenshots/prometheusDashboard.png)

![prometheus 2](./screenshots/prometheusDashBoard2.png)

![prometheus 3](./screenshots/prometheusDashBoard3.png)

- Metrics for python web app

![python app](./screenshots/pythonAppMetrics.png)

## Service configuration updates

I added the following mechanism to docker-compose.yml

```yml
x-logging:
  &default-logging
  driver: "json-file"
  options:
    tag: "{{.ImageName}}|{{.Name}}"
    max-size: '50m'
    max-file: '5'
```

For memory  added

```yml
x-deploy:
  &default-deploy
  resources:
    limits:
      memory: 200M
```

## Healthceck

For health check I added the following script

```yml
healthcheck:
    test: [ "CMD-SHELL", "curl --fail http://localhost:{port}/ || exit 1" ]
    interval: 1m
    timeout: 15s
    retries: 3
    start_period: 15s
```