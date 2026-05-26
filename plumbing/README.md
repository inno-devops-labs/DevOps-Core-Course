# `plumbing/` — Instructor-Maintained Services

This directory contains small services the **course** ships and maintains. Students
deploy them alongside their own service from Lab 9 onwards; students do **not** modify
the source.

The directory is **not gitignored** — it's a first-class part of the course repo, like
the lecture and lab markdown.

| Service | Port | Introduced in | Role |
|---------|------|---------------|------|
| [`echo/`](./echo) | 8081 | Lab 9 | 2nd pod — makes `Service`, kube-DNS, label selectors meaningful |
| [`health/`](./health) | 8082 | Lab 13 | 3rd pod — gives ArgoCD ApplicationSet enough targets to demonstrate the pattern |

## Why two extra services?

Through Lab 8 students run a **single** Python service. Modern DevOps is a
multi-service game, so the curriculum introduces additional services at the moments
where they *teach a concept*:

* **Lab 9 (Kubernetes Fundamentals)** — a `Service` + kube-DNS is only interesting
  when there are two pods to mediate between. `echo` is the smallest such companion.
* **Lab 13 (GitOps with ArgoCD)** — `ApplicationSet` and "App-of-Apps" patterns
  only pay off at ≥ 3 apps. `health` provides the third.

Both services are Go-based (fast cold start, tiny distroless image, ~15 MB). They
expose Prometheus metrics so Labs 7-8-16's observability stack picks them up
automatically.

## Building

Each service has its own `Dockerfile`. CI builds and publishes them to GHCR as the
course evolves:

* `ghcr.io/inno-devops-labs/echo:vX.Y.Z`
* `ghcr.io/inno-devops-labs/health:vX.Y.Z`

Labs reference these images by tag — students don't rebuild plumbing.
