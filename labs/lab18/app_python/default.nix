# default.nix — Nix derivation for the DevOps Info Service (FastAPI)
#
# This file replaces the traditional `pip install -r requirements.txt` workflow
# from Lab 1. Instead of resolving dependencies at runtime, Nix pins every
# package (including transitive deps) at evaluation time, producing a
# content-addressable store path that is bit-for-bit identical on any machine.
#
# Key fields:
#   pkgs              — nixpkgs attribute set, injected via the function argument
#   buildPythonApplication — builds a Python app (not a library)
#   pname / version   — used to compute the store path name component
#   src               — source tree; `./.` means "this directory"
#   format = "other"  — tells Nix we have no setup.py / pyproject.toml
#   propagatedBuildInputs — runtime Python dependencies (replaces requirements.txt)
#   nativeBuildInputs — build-time tools (makeWrapper wraps the script with the
#                       correct PYTHONPATH so the interpreter finds all packages)
#   installPhase      — custom install steps (copy app.py, wrap with Python)
#
# Reproducibility note:
#   When called via `nix-build`, pkgs defaults to `<nixpkgs>` from NIX_PATH.
#   For guaranteed reproducibility, use the Flake workflow instead:
#     nix build .#default   (uses flake.lock to pin exact nixpkgs revision)
#   The flake.lock file records the exact nixpkgs commit hash, ensuring
#   bit-for-bit identical builds across machines and time.

{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname   = "devops-info-service";
  version = "1.0.0";

  # Source is the current directory (labs/lab18/app_python/)
  src = ./.;

  # No setup.py / pyproject.toml — we handle installation manually below
  format = "other";

  # ── Runtime dependencies ────────────────────────────────────────────────────
  # These correspond to the packages in requirements.txt, but resolved from the
  # pinned nixpkgs snapshot rather than PyPI.  Nix pins the *entire* dependency
  # tree (including Werkzeug, anyio, starlette, etc.) — something requirements.txt
  # cannot guarantee for transitive dependencies.
  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi                          # Web framework (≈ fastapi==0.122.0 in req.txt)
    uvicorn                          # ASGI server  (≈ uvicorn[standard]==0.38.0)
    python-json-logger               # JSON logging (≈ python-json-logger==3.3.0)
    prometheus-fastapi-instrumentator # Prometheus metrics middleware
    prometheus-client                # Prometheus client library
  ];

  # ── Build-time tools ────────────────────────────────────────────────────────
  # makeWrapper generates a shell wrapper that sets PYTHONPATH so the Python
  # interpreter can locate all propagatedBuildInputs at runtime.
  nativeBuildInputs = [ pkgs.makeWrapper ];

  # ── Install phase ───────────────────────────────────────────────────────────
  # Nix builds happen in a sandbox with no network access.  We simply copy
  # app.py into $out/bin and wrap it so it runs with the correct interpreter.
  installPhase = ''
    mkdir -p $out/app $out/bin

    # Copy the application module so uvicorn can import it
    cp app.py $out/app/app.py

    # Create a launcher shell script that invokes uvicorn with the correct module
    cat > $out/bin/devops-info-service << 'EOF'
#!/bin/sh
exec uvicorn app:app --host "''${HOST:-0.0.0.0}" --port "''${PORT:-8000}"
EOF
    chmod +x $out/bin/devops-info-service

    # Wrap the launcher: inject PYTHONPATH (so `import fastapi` works) and
    # prepend the Nix Python + uvicorn bin dir to PATH.
    wrapProgram $out/bin/devops-info-service \
      --set   PYTHONPATH "$PYTHONPATH:$out/app" \
      --prefix PATH : "${pkgs.python3Packages.uvicorn}/bin" \
      --prefix PATH : "${pkgs.python3}/bin"
  '';

  # Skip the default check phase (no pytest configured for Nix build)
  doCheck = false;

  meta = with pkgs.lib; {
    description = "DevOps Info Service — FastAPI app built reproducibly with Nix";
    license     = licenses.mit;
    platforms   = platforms.all;
  };
}
