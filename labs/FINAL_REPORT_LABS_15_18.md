# Final Report - Labs 15-18

Run date: May 7, 2026

## Repository State

Branches were checked and pushed in order:

| Branch | Status |
| --- | --- |
| `lab15` | checked, already synchronized with `origin/lab15` |
| `lab16` | checked and pushed to `origin/lab16` |
| `lab17` | updated for current Cloudflare Workers task and pushed to `origin/lab17` |
| `lab18` | updated for current Nix task, includes merge from `lab17`, and pushed to `origin/lab18` |

Branch chain:

```text
lab15 -> lab16 -> lab17 -> lab18
```

Verified with:

```powershell
git merge-base --is-ancestor lab15 lab16
git merge-base --is-ancestor lab16 lab17
git merge-base --is-ancestor lab17 lab18
```

All checks returned success.

## Upstream Sync

The repository was fetched from both remotes:

```powershell
git fetch --all --prune
```

`upstream/master` was already contained in `lab15`, and therefore also contained in the later branches through the lab chain. This mattered because upstream changed Lab 17 and Lab 18:

- Lab 17 changed from Fly.io to Cloudflare Workers.
- Lab 18 changed from IPFS/4EVERLAND to Nix reproducible builds.

Both solutions were updated accordingly.

## Lab 15 - StatefulSets

Implementation already matched the current task:

- StatefulSet template
- headless Service
- per-pod `volumeClaimTemplates`
- StatefulSet values profiles
- partitioned rolling update profile
- `OnDelete` profile
- `k8s/STATEFULSET.md`

Validation:

```powershell
.\.tools\helm.exe lint .\k8s\devops-info-service
.\.tools\helm.exe template devops-info-service-stateful .\k8s\devops-info-service -f .\k8s\devops-info-service\values-statefulset.yaml --namespace stateful
.\.tools\helm.exe template devops-info-service-stateful .\k8s\devops-info-service -f .\k8s\devops-info-service\values-statefulset-partitioned.yaml --namespace stateful
.\.tools\helm.exe template devops-info-service-stateful .\k8s\devops-info-service -f .\k8s\devops-info-service\values-statefulset-ondelete.yaml --namespace stateful
```

Result:

```text
1 chart(s) linted, 0 chart(s) failed
```

## Lab 16 - Monitoring and Init Containers

Implementation already matched the current task:

- `k8s/monitoring/namespace.yaml`
- `k8s/monitoring/install-values.yaml`
- `ServiceMonitor` template
- monitoring StatefulSet values profile
- init container patterns for wait-for-service and download-to-shared-volume
- `k8s/MONITORING.md`

Validation:

```powershell
.\.tools\helm.exe lint .\k8s\devops-info-service
.\.tools\helm.exe template devops-info-service-monitoring .\k8s\devops-info-service -f .\k8s\devops-info-service\values-monitoring-statefulset.yaml --namespace stateful
.\.tools\helm.exe repo update
.\.tools\helm.exe template monitoring prometheus-community/kube-prometheus-stack --namespace monitoring -f .\k8s\monitoring\install-values.yaml
py -m pytest app_python\tests
```

Result:

```text
40 passed
1 chart(s) linted, 0 chart(s) failed
```

## Lab 17 - Cloudflare Workers

Updated because the upstream task changed.

Implemented:

- Cloudflare Workers TypeScript API
- `wrangler.jsonc`
- typed Worker bindings
- routes `/`, `/health`, `/edge`, `/config`, `/secrets`, `/counter`
- KV-backed counter code
- secret binding checks without committing secret values
- request logging for `wrangler tail`
- `WORKERS.md` report

Removed:

- old `app_python/fly.toml`

Validation:

```powershell
cd .\labs\lab17\edge-api
npm install
npm run typecheck
npm run deploy:dry-run
```

Result:

```text
found 0 vulnerabilities
tsc --noEmit
Total Upload: 3.57 KiB / gzip: 1.35 KiB
--dry-run: exiting now.
```

Live Cloudflare deploy still requires account authentication, real KV namespace IDs, and secrets. These values are not committed to Git.

## Lab 18 - Nix Reproducible Builds

Updated because the upstream task changed.

Implemented:

- copied Lab 1/2 Python app into `labs/lab18/app_python`
- `default.nix`
- `docker.nix`
- `flake.nix`
- `labs/submission18.md`

Removed:

- old IPFS/4EVERLAND demo files

Available validation:

```powershell
py -m pytest app_python\tests
.\.tools\helm.exe lint .\k8s\devops-info-service
cd .\labs\lab17\edge-api
npm run typecheck
npm run deploy:dry-run
```

Result:

```text
40 passed
1 chart(s) linted, 0 chart(s) failed
Worker dry-run deploy succeeded
```

Nix-specific output hashes were not fabricated because `nix` is not installed in this local environment. `labs/submission18.md` contains the exact command sequence to run on a Nix-enabled host.

## Final Notes

The repository side is clean and pushed. The remaining external evidence depends on services or tooling outside the repository:

- Cloudflare account deployment evidence for Lab 17
- Nix build/hash screenshots for Lab 18
- PR/Moodle submission links if required by the course platform
