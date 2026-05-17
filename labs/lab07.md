# Lab 7 — Observability & Logging with Loki Stack

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Logging%20%26%20Observability-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-Loki%20|%20Promtail%20|%20Grafana-informational)

> Deploy a logging stack with Loki, Promtail, and Grafana to aggregate and visualize logs from your containerized applications.

## Overview

Set up centralized logging for your applications using the Grafana Loki stack. You'll deploy Loki 3.0 (log storage with TSDB), Promtail (log collector), and Grafana 11 (visualization), then integrate your apps from previous labs.

**What You'll Learn:**
- Loki 3.0 architecture with TSDB (10x faster queries!)
- Promtail configuration for Docker log collection
- LogQL query language basics
- Building interactive log dashboards in Grafana 11
- Production logging practices and retention policies

**Prerequisites:** Lab 1 (web apps), Lab 2 (Docker), Lab 6 (Docker Compose understanding)

**Tech Stack:** Loki 3.0 + Promtail 3.0 + Grafana 12.3

---

## Tasks

### Task 1 — Deploy Loki Stack (4 pts)

Create a Docker Compose stack with Loki, Promtail, and Grafana.

#### 1.1 Study the Stack

**Research these components before starting:**
- [Loki Overview](https://grafana.com/docs/loki/latest/get-started/overview/) - How Loki works
- [Promtail Basics](https://grafana.com/docs/loki/latest/send-data/promtail/) - Log collection
- [LogQL Introduction](https://grafana.com/docs/loki/latest/query/) - Query language

**Understand:**
- How is Loki different from Elasticsearch?
- What are log labels and why do they matter?
- How does Promtail discover containers?

#### 1.2 Create Project Structure

```
monitoring/
├── docker-compose.yml
├── loki/
│   └── config.yml
├── promtail/
│   └── config.yml
└── docs/
    └── LAB07.md
```

#### 1.3 Configure Docker Compose

**File:** `monitoring/docker-compose.yml`

**Requirements:**
- Loki service (image: `grafana/loki:3.0.0`, port 3100)
- Promtail service (image: `grafana/promtail:3.0.0`)
- Grafana service (image: `grafana/grafana:12.3.1`, port 3000)
- Volumes for configs and data persistence
- Shared network

<details>
<summary>💡 Docker Compose Hints</summary>

**Key points to consider:**
- Use Docker Compose v2 syntax (version field is optional but use 3.8 for compatibility)
- Mount config files to `/etc/loki/config.yml` and `/etc/promtail/config.yml`
- Promtail needs access to Docker logs: `/var/lib/docker/containers:ro`
- Promtail needs Docker socket: `/var/run/docker.sock:ro` (⚠️ security consideration)
- Create named volumes: `loki-data` and `grafana-data`
- Use `command:` to specify config file path (e.g., `-config.file=/etc/loki/config.yml`)

**Grafana environment variables for easier testing:**
```yaml
environment:
  - GF_AUTH_ANONYMOUS_ENABLED=true
  - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
  - GF_SECURITY_ALLOW_EMBEDDING=true  # For iframe embedding if needed
```
⚠️ Only for development! Remove for production.

**Note:** Use `docker compose` (space, not hyphen) - the v2 CLI standard.

</details>

#### 1.4 Configure Loki

**File:** `monitoring/loki/config.yml`

**Research and configure:**
- Basic server settings (port 3100)
- Storage backend (use `tsdb` with `filesystem` - recommended in Loki 3.0)
- Schema configuration (use schema v13, find examples in [Loki docs](https://grafana.com/docs/loki/latest/configure/))
- Log retention: 7 days (168h)

<details>
<summary>💡 Loki Configuration Hints</summary>

**Essential sections you need:**
- `auth_enabled: false` (for testing)
- `server:` - HTTP port
- `common:` - Shared configuration (new in Loki 3.0, simplifies config)
- `schema_config:` - Storage schema (use v13 with TSDB for Loki 3.0+)
- `storage_config:` - Where to store data
  - Use `tsdb` index type (faster than boltdb-shipper)
  - Use `filesystem` object store for single-instance setup
- `limits_config:` - Retention period (`retention_period: 168h` = 7 days)
- `compactor:` - Cleanup old logs (required when retention is enabled)

**TSDB Benefits (Loki 3.0+):**
- Faster queries (up to 10x improvement)
- Lower memory usage
- Better compression

**Check the [Loki 3.0 configuration docs](https://grafana.com/docs/loki/latest/configure/) for structure and required fields.**

</details>

#### 1.5 Configure Promtail

**File:** `monitoring/promtail/config.yml`

**Requirements:**
- Configure Loki client endpoint (http://loki:3100)
- Set up Docker service discovery
- Add relabeling to extract container name as label

<details>
<summary>💡 Promtail Configuration Hints</summary>

**Key sections:**
- `server:` - Promtail's own port (9080)
- `positions:` - Track what logs were read
- `clients:` - Where to send logs (Loki URL + `/loki/api/v1/push`)
- `scrape_configs:` - How to collect logs

**For Docker service discovery:**
```yaml
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
```

**Relabeling extracts container name:**
- Use `__meta_docker_container_name` source label
- Create `container` target label
- Remove leading `/` from container name with regex

Check [Promtail Docker SD docs](https://grafana.com/docs/loki/latest/send-data/promtail/configuration/#docker_sd_configs).

</details>

#### 1.6 Deploy and Verify

**Deploy the stack:**
```bash
cd monitoring
docker compose up -d  # v2 CLI (space, not hyphen)
docker compose ps
```

**Verify services:**
```bash
# Test Loki
curl http://localhost:3100/ready

# Check Promtail targets
curl http://localhost:9080/targets

# Access Grafana
open http://localhost:3000
```

**In Grafana:**
1. Go to **Connections** → **Data sources** → **Add data source** → **Loki**
2. URL: `http://loki:3100`
3. Click **Save & Test** (should show "Data source connected")
4. Navigate to **Explore** → Select **Loki** data source
5. Query: `{job="docker"}` → You should see logs from all containers

**Alternative:** Provision the data source automatically (see bonus task for Ansible example).

**Evidence:** Screenshot showing logs from at least 3 containers in Grafana Explore.

---

### Task 2 — Integrate Your Applications (3 pts)

Add your apps to the logging stack and implement structured logging.

#### 2.1 Add Structured Logging

**Update your Python app** from Lab 1 to log in JSON format.

**Requirements:**
- Use Python's `logging` module
- Output JSON format: `{"timestamp": "...", "level": "...", "message": "...", ...}`
- Log important events: startup, HTTP requests, errors
- Include context: method, path, status code, client IP

<details>
<summary>💡 JSON Logging Hints</summary>

**Option 1: Custom formatter**
Create a `JSONFormatter` class that inherits from `logging.Formatter` and overrides the `format()` method to return JSON.

**Option 2: Use python-json-logger**
```bash
pip install python-json-logger
```
Then configure it in your app.

**What to log:**
- App startup with configuration
- Each HTTP request (use `@app.before_request`)
- Response status (use `@app.after_request`)
- Errors and exceptions

**Why JSON?**
- Easy to parse by log aggregation tools
- Structured data, not just text
- Can extract fields in LogQL queries

</details>

#### 2.2 Add Applications to Docker Compose

**Extend** `monitoring/docker-compose.yml` with your applications:
- Python app from Lab 1 (port 8000)
- Bonus app from Lab 1 if you completed it (port 8001)

**Both apps should:**
- Join the `logging` network
- Have labels for Promtail filtering: `logging: "promtail"`, `app: "app-name"`

<details>
<summary>💡 Multi-App Compose Hints</summary>

**Add to your docker-compose.yml:**
```yaml
services:
  # ... loki, promtail, grafana ...

  app-python:
    image: your-username/devops-info-service:latest
    ports:
      - "8000:8000"
    networks:
      - logging
    labels:
      logging: "promtail"
      app: "devops-python"
```

**Filter in Promtail:** Update `promtail/config.yml` to only scrape containers with the label:
```yaml
filters:
  - name: label
    values: ["logging=promtail"]
```

</details>

#### 2.3 Generate Logs and Test

**Make requests to generate logs:**
```bash
# Generate traffic
for i in {1..20}; do curl http://localhost:8000/; done
for i in {1..20}; do curl http://localhost:8000/health; done
```

**Query logs in Grafana Explore:**
```logql
# All logs from Python app
{app="devops-python"}

# Only errors
{app="devops-python"} |= "ERROR"

# Parse JSON and filter
{app="devops-python"} | json | method="GET"
```

**Evidence:**
- Screenshot of JSON log output from your app
- Screenshot of Grafana showing logs from both applications
- At least 3 different LogQL queries that work

---

### Task 3 — Build Log Dashboard (2 pts)

Create a Grafana dashboard to visualize your application logs.

#### 3.1 Learn LogQL Basics

**Practice these query patterns in Explore first:**

1. **Stream selection:** `{app="devops-python"}`
2. **Text filtering:** `{app="devops-python"} |= "error"`
3. **JSON parsing:** `{app="devops-python"} | json`
4. **Field filtering:** `{app="devops-python"} | json | level="INFO"`
5. **Metrics from logs:** `rate({app="devops-python"}[1m])`

<details>
<summary>💡 LogQL Reference</summary>

**Stream selectors:**
- `{label="value"}` - exact match
- `{label=~"regex"}` - regex match
- `{label!="value"}` - not equal

**Line filters:**
- `|= "text"` - contains
- `!= "text"` - doesn't contain
- `|~ "regex"` - regex match

**Parsers:**
- `| json` - parse JSON logs
- `| logfmt` - parse logfmt logs

**Aggregations:**
- `rate({app="app"}[5m])` - logs per second
- `count_over_time({app="app"}[5m])` - count logs
- `sum by (level) (count_over_time({app="app"} | json [5m]))` - count by level

Learn more: [LogQL Documentation](https://grafana.com/docs/loki/latest/query/)

</details>

#### 3.2 Create Dashboard

**Requirements - create 4 panels:**

1. **Logs Table** (Logs visualization)
   - Shows recent logs from all apps
   - Query: `{app=~"devops-.*"}`

2. **Request Rate** (Time series graph)
   - Shows logs per second by app
   - Query: `sum by (app) (rate({app=~"devops-.*"} [1m]))`

3. **Error Logs** (Logs visualization)
   - Shows only ERROR level logs
   - Query: `{app=~"devops-.*"} | json | level="ERROR"`

4. **Log Level Distribution** (Stat or Pie chart)
   - Count logs by level (INFO, ERROR, etc.)
   - Query: `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`

**How to create:**
1. **Dashboard** → **New** → **New Dashboard** → **Add visualization**
2. Select **Loki** data source
3. Enter LogQL query (use the query builder or code editor)
4. Choose visualization type (Logs, Time series, Stat, Pie chart, etc.)
5. Configure panel title and options
6. **Save dashboard** (Grafana 11 auto-saves drafts)

**Grafana 11 features:**
- Query builder UI for LogQL (easier for beginners)
- Better log context and line wrapping
- Improved variable support
- Dashboard version history

**Evidence:** Screenshot of your dashboard showing all 4 panels with real data.

---

### Task 4 — Production Readiness (1 pt)

Configure the stack for production use.

#### 4.1 Add Resource Limits

Add resource constraints to prevent services from consuming too much:

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

**Apply to all services** with appropriate values.

#### 4.2 Secure Grafana

**Remove anonymous authentication:**
- Change `GF_AUTH_ANONYMOUS_ENABLED` to `false`
- Set admin password via environment variable
- Use `.env` file for secrets (don't commit!)

#### 4.3 Add Health Checks

Add `healthcheck:` sections to verify services are working:
- Loki: `http://localhost:3100/ready`
- Grafana: `http://localhost:3000/api/health`

<details>
<summary>💡 Health Check Example</summary>

```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3100/ready || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s  # Grace period for startup
```

**Alternative using curl:**
```yaml
test: ["CMD-SHELL", "curl -f http://localhost:3100/ready || exit 1"]
```

</details>

**Evidence:**
- `docker-compose ps` showing all services healthy
- Screenshot of Grafana login page (no anonymous access)

---

### Task 5 — Documentation (2 pts)

Create `monitoring/docs/LAB07.md` documenting your setup.

**Required sections:**
1. **Architecture** - Diagram showing how components connect
2. **Setup Guide** - Step-by-step deployment instructions
3. **Configuration** - Explain your Loki/Promtail configs and why
4. **Application Logging** - How you implemented JSON logging
5. **Dashboard** - Explain each panel and the LogQL queries
6. **Production Config** - Security measures, resources, retention
7. **Testing** - Commands to verify everything works
8. **Challenges** - Problems you encountered and solutions

**Include:**
- Configuration file snippets (not full files)
- Screenshots of Grafana dashboard
- Example LogQL queries with explanations
- Evidence of all tasks completed

---

## Bonus — Ansible Automation (2.5 pts)

Automate Loki stack deployment with Ansible (builds on Labs 5-6).

**Create Ansible role** `roles/monitoring` that:
- Creates monitoring directory structure
- Templates configuration files (Loki 3.0 format)
- Deploys stack with Docker Compose v2
- Waits for services to be ready
- Configures Grafana data source

**Requirements:**
- Use Jinja2 templates for configs (versions, ports, retention as variables)
- Make it idempotent (use `community.docker.docker_compose_v2` module)
- Add to your existing Ansible setup from Lab 6
- Create playbook: `playbooks/deploy-monitoring.yml`
- Compatible with Ansible 2.16+

<details>
<summary>💡 Ansible Role Structure</summary>

```
roles/monitoring/
├── defaults/main.yml       # Variables (versions, ports, etc.)
├── tasks/
│   ├── main.yml           # Main orchestration
│   ├── setup.yml          # Create dirs, template configs
│   └── deploy.yml         # Docker compose deployment
├── templates/
│   ├── docker-compose.yml.j2
│   ├── loki-config.yml.j2
│   └── promtail-config.yml.j2
└── meta/main.yml          # Depends on: docker role
```

**Key variables to parameterize:**
- Service versions (loki: 3.0.0, promtail: 3.0.0, grafana: 11.3.0)
- Ports (loki: 3100, grafana: 3000, promtail: 9080)
- Retention period (default: 168h / 7 days)
- Resource limits (memory, CPU)
- Schema version (v13 for Loki 3.0+)

</details>

**Evidence:**
- Ansible playbook execution output
- Idempotency test (run twice, second shows no changes)
- Templated configuration files

---

## Checklist

**Before submitting:**
- [ ] Loki, Promtail, Grafana running via Docker Compose
- [ ] Loki data source configured in Grafana
- [ ] Python app logging in JSON format
- [ ] Bonus app (if completed Lab 1 bonus) integrated
- [ ] Logs visible in Grafana from all containers
- [ ] Dashboard with 4+ panels created
- [ ] LogQL queries working for different scenarios
- [ ] Resource limits on all services
- [ ] Health checks added
- [ ] Grafana secured (no anonymous access)
- [ ] Complete documentation with screenshots
- [ ] All configuration files in repo

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Stack Deployment** | 4 pts | Loki, Promtail, Grafana configured and working |
| **App Integration** | 3 pts | Apps logging JSON format, visible in Loki |
| **Dashboard** | 2 pts | 4+ panels with appropriate LogQL queries |
| **Production Config** | 1 pt | Resources, security, health checks |
| **Documentation** | 2 pts | Complete LAB07.md with evidence |
| **Bonus: Ansible** | 2.5 pts | Automated deployment with Ansible role |
| **Total** | 12.5 pts | 10 pts required + 2.5 bonus |

---

## Resources

<details>
<summary>📚 Loki Documentation</summary>

- [Loki 3.0 Overview](https://grafana.com/docs/loki/latest/get-started/overview/)
- [Loki Configuration](https://grafana.com/docs/loki/latest/configure/)
- [LogQL Query Language](https://grafana.com/docs/loki/latest/query/)
- [Storage Configuration](https://grafana.com/docs/loki/latest/storage/)

</details>

<details>
<summary>🚢 Promtail</summary>

- [Promtail Configuration](https://grafana.com/docs/loki/latest/send-data/promtail/configuration/)
- [Docker Service Discovery](https://grafana.com/docs/loki/latest/send-data/promtail/configuration/#docker_sd_configs)
- [Scraping Configuration](https://grafana.com/docs/loki/latest/send-data/promtail/scraping/)

</details>

<details>
<summary>📊 Grafana</summary>

- [Grafana 11 Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [Loki Data Source](https://grafana.com/docs/grafana/latest/datasources/loki/)
- [Explore Logs](https://grafana.com/docs/grafana/latest/explore/logs-integration/)

</details>

<details>
<summary>📝 Logging Best Practices</summary>

- [Structured Logging with structlog](https://www.structlog.org/en/stable/)
- [The Twelve-Factor App: Logs](https://12factor.net/logs)
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [python-json-logger](https://github.com/madzak/python-json-logger)

</details>

---

## Looking Ahead

- **Lab 8:** Metrics with Prometheus - Add metrics to complement logs
- **Lab 9:** Kubernetes Fundamentals - Deploy your apps to K8s
- **Lab 10-12:** Helm, Secrets, ConfigMaps - Package and configure K8s deployments
- **Lab 16:** Kubernetes Monitoring - Full observability in K8s

---

**Good luck!** 🚀
