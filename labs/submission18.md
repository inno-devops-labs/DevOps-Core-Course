# Lab 18 — Reproducible Builds with Nix

## 1. Goal

The goal of this lab is to rebuild the existing DevOps Info Service from Labs 1-2 using Nix and compare this approach with the traditional `pip + venv` and Dockerfile workflows.

The submitted application is placed in:

```text
labs/lab18/app_python/
```

It is based on the existing FastAPI application from `app_python/`.

## 2. Prepared Files

```text
labs/lab18/app_python/
├── app.py
├── config.py
├── default.nix
├── docker.nix
├── Dockerfile
├── requirements.txt
├── routes/
├── services/
└── tests/
```

Important Nix files:

| File | Purpose |
|------|---------|
| `default.nix` | Builds the FastAPI app as a Nix package |
| `docker.nix` | Builds a reproducible Docker image using `dockerTools` |

## 3. Traditional Lab 1 Approach

In Lab 1 the app was started through Python and pip:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

This is simple, but not fully reproducible:

- the system Python version can be different;
- transitive dependencies can drift;
- virtual environments are not portable;
- the result depends on the state of PyPI at installation time.

## 4. Nix Package Build

The Nix package is defined in `labs/lab18/app_python/default.nix`.

Key parts:

```nix
pythonPackages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pythonPackages; [
    fastapi
    uvicorn
    prometheus-client
  ];
}
```

The app is installed into the Nix store and wrapped as:

```text
result/bin/devops-info-service
```

Commands to build and run:

```bash
cd labs/lab18/app_python
nix-build
./result/bin/devops-info-service
```

Expected app URL:

```text
http://localhost:8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## 5. Reproducibility Check

Commands:

```bash
cd labs/lab18/app_python

nix-build
readlink result
nix-hash --type sha256 result

rm result
nix-build
readlink result
nix-hash --type sha256 result
```

Expected result:

- both `readlink result` outputs should point to the same Nix store path;
- both `nix-hash` outputs should be identical;
- this proves that the same inputs produce the same output.

Evidence to paste after running Nix:

```text
First build store path:
TODO: paste readlink result

Second build store path:
TODO: paste readlink result

First output hash:
TODO: paste nix-hash output

Second output hash:
TODO: paste nix-hash output
```

## 6. Docker Image with Nix

The reproducible Docker image is defined in:

```text
labs/lab18/app_python/docker.nix
```

Build command:

```bash
cd labs/lab18/app_python
nix-build docker.nix
```

Load into Docker:

```bash
docker load < result
```

Run:

```bash
docker run --rm -p 8000:8000 devops-info-service-nix:1.0.0
```

Test:

```bash
curl http://localhost:8000/health
```

Reproducibility check:

```bash
sha256sum result
rm result
nix-build docker.nix
sha256sum result
```

Expected result: both tarball hashes should be identical.

## 7. Traditional Dockerfile vs Nix dockerTools

| Aspect | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|--------|------------------|------------------------|
| Base image | `python:3.13-slim` tag can change over time | Built from pinned Nix packages |
| Dependencies | Installed by `pip install` during image build | Declared in Nix derivation |
| Timestamps | Docker layers usually include build-time metadata | `created` timestamp is fixed |
| Rebuild hash | Can differ between builds | Should be identical for same inputs |
| Dependency graph | Partially visible through pip | Fully represented by Nix closure |
| Rollback | Depends on image tags | Store paths are content-addressed |

## 8. Comparison with Helm Values from Lab 10

In Lab 10, Helm values pinned the image tag:

```yaml
image:
  repository: roma3213/info_service
  tag: "latest"
```

This is useful for deployment configuration, but it does not guarantee that the image contents are reproducible.

Nix derivations lock the build inputs more deeply:

- Python interpreter;
- Python libraries;
- build tools;
- package source revisions;
- Docker image contents when using `dockerTools`.

The best production approach would be:

1. build the image reproducibly with Nix;
2. push it using an immutable tag or digest;
3. reference that digest in Helm values.

## 9. Local Verification

The Python app tests pass locally outside Nix:

```text
12 passed
```

Nix itself was not available in the current Windows shell, so Nix store paths and hashes should be filled after running these files in Linux/WSL2 with Nix installed.

## 10. Conclusion

Nix improves the reproducibility of the Lab 1-2 application because dependencies and build instructions are declared in one deterministic build graph. Traditional `pip` and Docker workflows are practical and familiar, but they do not provide the same level of reproducibility unless every dependency, base image, and build timestamp is controlled.
