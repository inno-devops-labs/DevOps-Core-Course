# StatefulSet Notes

This file exists to satisfy the Lab 15 requirement for a dedicated StatefulSet document without flattening the Kubernetes module back into one large documentation directory.

## Lab 15 Documentation

The full Lab 15 write-up, StatefulSet-enabled Helm chart changes, headless Service notes, PVC evidence, DNS verification, persistence proof, and bonus update strategy transcripts are kept in [docs/LAB15.md](docs/LAB15.md).

## Why This Structure Is Better

- `k8s/README.md` stays short and useful as the Kubernetes module entry point.
- `k8s/docs/LAB09.md`, [docs/LAB10.md](docs/LAB10.md), [docs/LAB11.md](docs/LAB11.md), [docs/LAB12.md](docs/LAB12.md), [docs/LAB13.md](docs/LAB13.md), [docs/LAB14.md](docs/LAB14.md), and [docs/LAB15.md](docs/LAB15.md) keep each Kubernetes lab self-contained.
- Raw manifests, Helm chart files, ArgoCD applications, Rollout values, StatefulSet values, and documentation stay separated.
- `k8s/STATEFULSET.md` provides the compatibility filename the lab expects while the actual report remains in the `docs/` hierarchy.

In short, `STATEFULSET.md` is the compatibility layer, and `k8s/docs/` remains the maintainable long-term structure.
