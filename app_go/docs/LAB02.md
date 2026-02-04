# Lab 02 — Bonus Task: Go Multi-Stage Build

## Multi-Stage Strategy

I implemented a multi-stage build for the Go application.

**Stage 1 (Builder):** Uses ``golang:1.23-alpine`` to compile the source code into a static binary.

**Stage 2 (Runtime):** Uses ``alpine:3.20``. I copied ONLY the resulting binary from the builder.

## Size Analysis (Real Data)

Based on ``docker images`` output, here is the final comparison:

| Image Name | Tag   | Disk Usage | Content Size|
| -------- | --------- | ----------------------------------------------------------- | --------- | 
| ray326sq/app_go   | lab02 | 24.3 MB | 8.06 MB
|devops-info-python | latest | 182 MB | 44.4 MB
### Analysis

The Go image is approximately **7.5 times** smaller than the Python image in terms of total disk usage. The actual application content (``Content Size``) in Go is only **8.06 MB**, which is incredibly efficient for a microservice.

## Technical Explanation

* Static Compilation: By using CGO_ENABLED=0, I ensured the binary has no external dependencies on C libraries.

* Payload efficiency: Since Go compiles to native machine code, we don't need to ship an interpreter (like Python) or a virtual machine (like Java) inside the container.

* Security: The final image is minimal, containing no build tools, reducing the potential attack surface.

## Build Process Output
```
IMAGE                    ID              DISK USAGE    CONTENT SIZE
ray326sq/app_go:lab02    bbb215884742    24.3MB        8.06MB
```