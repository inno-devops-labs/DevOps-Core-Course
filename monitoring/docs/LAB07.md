# Lab 7 Documentation Report

## Architecture

The architecture for monitoring involves the following components:

1. **devops-app**:
   - A Python-based Flask application that generates structured logs.
   - Logs are emitted in JSON format using a custom `JsonFormatter`.

2. **Promtail**:
   - Acts as an agent to scrape logs from Docker containers.
   - Configures Docker socket (`/var/run/docker.sock`) for dynamic container discovery.
   - Forwards logs to Loki with labels like `container` and `compose_service`.

3. **Loki**:
   - Stores and indexes logs using a filesystem-based storage.
   - Retention period is set to 168 hours (7 days).
   - Schema version `v13` is used for efficient log indexing.

4. **Grafana**:
   - Provides a dashboard for visualizing logs and metrics.
   - Anonymous access is enabled for simplicity during development.

![alt](/monitoring/docs/flowchart.png)

## Setup Guide

To deploy the stack, follow these steps:

1. Navigate to the `monitoring` directory:
   ```bash
   cd monitoring
   ```

2. Create /monitoring/.env with the following content
  ```bash
  GRAFANA_ADMIN_USER=admin
  GRAFANA_ADMIN_PASSWORD=admin_password
  ```

3. Build and start the services using Docker Compose:
   ```bash
   docker-compose build && docker-compose up -d
   ```

4. Verify the deployment:
   - Grafana: Accessible at `http://localhost:3000`

## Configuration

### Loki Configuration (`loki/config.yml`)
- **Storage**:
  - Uses filesystem for storing chunks and rules.
  - Retention period is set to 7 days (`168h`).
  - Compaction is enabled with a retention policy.

- **Schema**:
  - Schema version `v13` is used, which supports efficient log indexing.

- **Replication**:
  - Replication factor is set to `1` for simplicity in this setup.

### Promtail Configuration (`monitoring/promtail/config.yml`)
- **Scrape Configurations**:
  - Dynamically discovers Docker containers using the Docker socket.
  - Refresh interval is set to `5s` for real-time log scraping.
  - Labels logs with container and compose service names for better filtering in Grafana.

## Application Logging

The application (`app.py`) implements structured JSON logging using a custom `JsonFormatter`. Key features include:

1. **Log Structure**:
   - Each log entry includes:
     - `timestamp`: ISO 8601 formatted timestamp in UTC.
     - `level`: Log level (e.g., `INFO`, `ERROR`).
     - `logger`: Logger name.
     - `message`: The log message.
     - Additional context like request details if provided via `extra`.

2. **Request Context**:
   - Request-specific information (e.g., IP, method, path) is included in logs using the `extra` field.

3. **Logging Levels**:
   - Logs are emitted at different levels based on HTTP response status codes:
     - Server errors (5xx): Trigger `ERROR` logs.
     - Client errors (4xx): Trigger `WARNING` logs.
     - Successful requests: Trigger `INFO` logs.

## Dashboard

![alt](/monitoring/docs/explore_devops-app.png)

![alt](/monitoring/docs/explore_promtail.png)

![alt](/monitoring/docs/explore_loki.png)

![alt](/monitoring/docs/explore_grafana.png)

![alt](/monitoring/docs/dashboard.png)

![alt](/monitoring/docs/grafana_login.png)

## Production Config

### Security Measures
- **Grafana**:
  - Anonymous access is disabled (`GF_AUTH_ANONYMOUS_ENABLED=false`).
  - Admin credentials specified in `monitoring/.env` but better measures (oauth) should be implemented for prod.

### Resource Limits
  - Explicit resource limits are set for all services.
  - `docker-compose.yml`:
    ```yaml
    resources:
      limits:
        cpus: '1'
        memory: 1G
      reservations:
        cpus: '0.5'
        memory: 512M
    ```

### Retention Policies
- **Loki**:
  - Logs are retained for 7 days (`retention_period: 168h`).
  - Compaction is enabled with a retention policy to manage storage efficiently.

### Health Checks
  - All monitoring services has healthchecks setted up in `monitoring/docker-compose.yml` 
  ```bash
  CONTAINER ID   IMAGE                           COMMAND                  CREATED          STATUS                      PORTS                                         NAMES
  695738af8bb7   grafana/promtail:3.0.0          "/usr/bin/promtail -…"   40 minutes ago   Up 40 minutes (healthy)                                                 promtail
  724314b54f0f   grafana/grafana:12.3.1          "/run.sh"                40 minutes ago   Up 40 minutes (healthy)     0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp   grafana
  5d73a8763c15   monitoring-app                  "python app.py"          40 minutes ago   Up 40 minutes               0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp   devops-app
  9ef411117d9b   grafana/loki:3.0.0              "/usr/bin/loki -conf…"   40 minutes ago   Up 40 minutes (healthy)     0.0.0.0:3100->3100/tcp, [::]:3100->3100/tcp   loki
  ```

## Testing

To test the setup, follow these steps:

1. **Generate Logs**:
   - Access the application at `http://localhost:5000`.
   - Trigger different HTTP responses (e.g., GET `/`, GET `/health`) to generate logs of varying levels (`INFO`, `WARNING`, `ERROR`).

2. **Verify Logs in Grafana**:
   - Open Grafana at `http://localhost:3000`.
   - Use LogQL queries to explore the logs, e.g.:
     ```logql
     {container="devops-app"} |= "info"
     ```
   - Verify that logs are correctly labeled with container and service names.

## Challenges

No real challenges were encountered during the lab solution. The setup was straightforward, and all components (Loki, Promtail, Grafana) mostly worked as expected.
