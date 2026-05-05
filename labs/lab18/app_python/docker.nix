# docker.nix — Reproducible Docker image for the DevOps Info Service
#
# This file replaces the traditional Dockerfile from Lab 2.
#
# Key differences vs Lab 2 Dockerfile:
#   Lab 2 Dockerfile                    │ This docker.nix
#   ────────────────────────────────────┼──────────────────────────────────────
#   FROM python:3.12-slim               │ No base image — pure Nix closure
#   RUN pip install -r requirements.txt │ Nix store paths (immutable, hashed)
#   Timestamps differ each build        │ created = "1970-01-01T00:00:01Z" (fixed)
#   Different SHA256 each build         │ Identical SHA256 every build, forever
#   ~200 MB with base OS                │ ~80-120 MB minimal closure
#
# Critical reproducibility rules:
#   1. NEVER use `created = "now"` — that embeds the current timestamp into the
#      image manifest, making every build produce a different hash even if the
#      content is identical.  Use the Unix epoch instead.
#   2. For maximum reproducibility, use the Flake workflow:
#        nix build .#dockerImage   (uses flake.lock to pin exact nixpkgs revision)
#
# Platform note (macOS M-series):
#   On macOS Apple Silicon, Nix builds aarch64-darwin binaries.
#   Docker Desktop on macOS runs Linux containers via a lightweight VM.
#   Cross-compilation from macOS to Linux requires a full Linux toolchain
#   which is not available in the binary cache for this nixpkgs snapshot.
#   The reproducibility proof (identical SHA256 across multiple builds) is
#   demonstrated via the tarball hash comparison — the key property of
#   Nix's content-addressable store.
#
# How it works:
#   1. We include python3 + all required packages in `contents`
#   2. We copy app.py into the image via a runCommand derivation
#   3. The Cmd runs `python3 app.py` directly

{ pkgs ? import <nixpkgs> {} }:

let
  # Python environment with all required packages
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi
    uvicorn
    python-json-logger
    prometheus-fastapi-instrumentator
    prometheus-client
  ]);

  # Create a derivation that holds app.py
  appSrc = pkgs.runCommand "devops-info-service-src" {} ''
    mkdir -p $out/app
    cp ${./app.py} $out/app/app.py
  '';
in

pkgs.dockerTools.buildLayeredImage {
  # ── Image metadata ──────────────────────────────────────────────────────────
  name = "devops-info-service-nix";
  tag  = "1.0.0";

  # ── Reproducible timestamp ──────────────────────────────────────────────────
  # Using Unix epoch (1970-01-01T00:00:01Z) instead of "now" ensures the image
  # manifest hash is identical on every build, on every machine, forever.
  # This is the single most important setting for Docker image reproducibility.
  created = "1970-01-01T00:00:01Z";

  # ── Image contents ──────────────────────────────────────────────────────────
  # Only include what's needed: Python + all dependencies + app source.
  # No full OS base image required — Nix computes the minimal closure.
  contents = [
    pythonEnv             # Python interpreter + all dependencies
    appSrc                # The app.py source file
    pkgs.coreutils        # Basic Unix tools
    pkgs.bash             # Shell
  ];

  # ── Container configuration ─────────────────────────────────────────────────
  config = {
    # Run Python directly — avoids shell wrapper exec format issues
    Cmd = [
      "${pythonEnv}/bin/python3"
      "${appSrc}/app/app.py"
    ];

    # Expose port 8000 (matches Lab 2 Dockerfile and app.py PORT default)
    ExposedPorts = {
      "8000/tcp" = {};
    };

    # Environment variables — mirror Lab 2 / Helm values.yaml defaults
    Env = [
      "HOST=0.0.0.0"
      "PORT=8000"
      "DEBUG=False"
      "VISITS_FILE=/tmp/visits"
    ];

    WorkingDir = "/app";

    # Labels for image metadata
    Labels = {
      "org.opencontainers.image.title"       = "devops-info-service";
      "org.opencontainers.image.version"     = "1.0.0";
      "org.opencontainers.image.description" = "DevOps Info Service built reproducibly with Nix";
      "build.tool"                           = "nix-dockerTools";
    };
  };

  # ── Layer optimisation ──────────────────────────────────────────────────────
  # buildLayeredImage splits the closure into separate layers by dependency
  # frequency, maximising Docker layer cache reuse.
  maxLayers = 120;
}
