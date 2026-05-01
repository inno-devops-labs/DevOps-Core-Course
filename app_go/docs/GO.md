# Why Go for the Bonus

- **Small static binaries:** Easy to ship as single artifacts and perfect for multi-stage Docker builds in later labs.
- **Fast startup and low memory:** Great for lightweight info services and health probes.
- **Standard library HTTP:** `net/http` avoids extra dependencies while staying production-ready.
- **Strong concurrency model:** Goroutines/channels enable future extensions (metrics, async tasks) without major rewrites.
- **Ecosystem fit:** Common in cloud-native tooling (Kubernetes, Prometheus, Terraform) so skills translate directly.

# Go binary vs Python

- Go: One self-contained ~10 MB binary (great for Docker and Kubernetes).
- Python: Tiny script, but depends on a much larger runtime. When containerized, the Python image is usually larger overall than a minimal Go image with just the compiled binary.