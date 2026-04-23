# Lab 17 — Fly.io Edge Deployment

## 1. Setup status

### CLI installation
```bash
brew install flyctl
fly version
```

Installed version:
```bash
fly v0.4.39 darwin/arm64
```

### Authentication check
```bash
fly auth whoami
```

Current result in this environment:
```bash
Error: no access token available. Please login with 'flyctl auth login'
```

Because Fly.io authentication is account-bound and interactive, deployment to real Fly infrastructure cannot be completed from this headless non-authenticated session.

## 2. Application prepared for Fly

Prepared files:
- `app_python/fly.toml`
- `app_python/fly-secrets.example.env`
- `app_python/scripts/fly-quickstart.sh`

### `fly.toml` highlights
- app name: `devops-core-course-lab17`
- primary region: `ams`
- internal port: `8080`
- health check: `GET /health`
- persistent mount: `/data`

### Local runtime verification
```bash
docker build -t devops-core-fly:test app_python
docker run -d -p 18090:8080 devops-core-fly:test
curl http://127.0.0.1:18090/health
```

Result:
```json
{"status":"healthy","timestamp":"2026-04-23T12:19:31.967587+00:00","uptime_seconds":0}
```

## 3. Deployment commands (ready after login)

Run from `app_python/`:
```bash
fly auth login
fly launch --no-deploy --copy-config
fly deploy
fly status
fly logs --no-tail
```

Expected deliverables after deploy:
- app URL (`fly open` / `fly status`)
- successful health checks on `/health`
- release history from `fly releases`

## 4. Multi-region and scaling

Commands prepared:
```bash
fly regions add iad sin
fly scale count 2 --region ams
fly machines list
fly status
```

Target: primary + at least two extra regions (`ams`, `iad`, `sin`).

## 5. Secrets and persistence

Secrets:
```bash
fly secrets set DATABASE_URL="postgres://..." API_KEY="..."
fly secrets list
```

Volume:
```bash
fly volumes create devops_info_data --size 1 --region ams
fly deploy
```

Persistence check:
```bash
fly ssh console
cat /data/visits
```

## 6. Monitoring and operations

```bash
fly status
fly logs
fly releases
fly deploy --strategy rolling
```

Health check is already configured in `fly.toml` via `[[http_service.checks]]` for `/health`.

## 7. Kubernetes vs Fly.io comparison

| Aspect | Kubernetes | Fly.io |
|---|---|---|
| Setup complexity | High (cluster + manifests/controllers) | Low (platform-managed runtime) |
| Deployment speed | Medium | Fast |
| Global distribution | Flexible but manual infra work | Native region model, simpler UX |
| Cost (small apps) | Can be higher operational overhead | Usually cheaper/simpler to start |
| Learning curve | Steep | Moderate |
| Control/flexibility | Maximum control | Opinionated constraints |
| Best use case | Complex multi-service/platform workloads | Small/medium apps needing global latency reduction quickly |

## 8. When to use each

Use Kubernetes when:
- you need custom controllers/operators, advanced networking/policy, complex platform-level control.

Use Fly.io when:
- you need fast global deployment with minimal ops overhead and can accept platform constraints.

## 9. Completion note for this environment

Done:
- Fly CLI installation and verification
- Fly config (`fly.toml`) and supporting files
- Local container build/runtime validation

Blocked by missing external auth:
- real `fly deploy`
- real multi-region machine placement evidence
- dashboard screenshots/metrics from Fly control plane

Once authenticated, run `app_python/scripts/fly-quickstart.sh` and attach outputs/screenshots to finalize runtime evidence.
