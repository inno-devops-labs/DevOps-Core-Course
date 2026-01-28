# Lab 01 (Bonus) — Go Implementation Details

## Overview

This implementation reproduces the functionality of the Python DevOps Info Service using Go's standard `net/http` package.

## Implementation Features

Zero Dependencies: The service uses only the Go standard library, ensuring maximum compatibility and security.

JSON Encoding: Used `encoding/json` for structured data responses, matching the exact schema of the Python version.

Reflective Metadata: Leveraged the `runtime` package to extract CPU count, Go version, and OS architecture.

Logging: Implemented basic request logging using the `log` package to track incoming traffic.

## Size Comparison

| Metric | Python (Flask + Venv)   | Go (Single Binary)|
| -------- | --------- | ----------------------------------------------------------- |
| Size   | 20,3 MB | 8,1 MB

## Binary Analysis

The Go binary is significantly smaller and easier to distribute. In a DevOps pipeline, this translates to faster Docker image builds, lower storage costs in registries, and quicker deployments (pull times) in cloud environments.