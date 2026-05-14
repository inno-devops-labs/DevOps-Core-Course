# Lab 18 — Task 1 (Python app)

This directory contains the Nix derivation for the Lab 1 Python service.

## Files

- `default.nix` — reproducible build expression for the Flask app

## How to build

```bash
cd labs/lab18/app_python
nix-build
```

## How to run the built app

```bash
./result/bin/devops-info-service
```

The app listens on `HOST` and `PORT` from the environment. By default it runs on:

- `HOST=0.0.0.0`
- `PORT=5000`

Then open:

- `http://localhost:5000/`
- `http://localhost:5000/health`
- `http://localhost:5000/metrics`
