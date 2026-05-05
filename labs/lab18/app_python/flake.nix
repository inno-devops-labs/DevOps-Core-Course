# flake.nix — Modern Nix Flake for the DevOps Info Service
#
# Flakes are the modern (2024+) standard for Nix projects.  They provide:
#   • Automatic dependency locking via flake.lock (like package-lock.json but
#     for the *entire* build toolchain, not just app dependencies)
#   • Standardised inputs/outputs schema understood by all Nix tooling
#   • Hermetic evaluation — no implicit access to ~/.nixpkgs or NIX_PATH
#   • Easy sharing: `nix build github:user/repo#package` works out of the box
#
# Comparison with Lab 10 Helm values.yaml:
#   Helm values.yaml pins:  image tag only (e.g. "1.0")
#   flake.lock pins:        nixpkgs git revision → all 80 000+ packages,
#                           Python version, build tools, compilers — everything
#
# Platform note (macOS M-series):
#   This flake targets aarch64-darwin (Apple Silicon).
#   Change `system` to "x86_64-darwin" for Intel Mac or "x86_64-linux" for Linux.
#   For multi-platform support see: https://github.com/numtide/flake-utils

{
  description = "DevOps Info Service — Reproducible Build with Nix Flakes";

  # ── Inputs ──────────────────────────────────────────────────────────────────
  # Each input is locked to an exact git revision in flake.lock.
  # `nix flake update` refreshes the lock; `nix flake lock --update-input nixpkgs`
  # updates only nixpkgs.
  inputs = {
    # Pin to nixos-24.11 stable channel for maximum reproducibility.
    # The exact commit is recorded in flake.lock after `nix flake update`.
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  # ── Outputs ─────────────────────────────────────────────────────────────────
  # `self`    — this flake itself (used for self-referential builds)
  # `nixpkgs` — the locked nixpkgs input
  outputs = { self, nixpkgs }:
    let
      # ── Platform selection ─────────────────────────────────────────────────
      # macOS Apple Silicon (M1/M2/M3/M4).
      # Change to "x86_64-darwin" (Intel Mac) or "x86_64-linux" (Linux/WSL2).
      system = "aarch64-darwin";

      # Instantiate nixpkgs for the target system.
      # `legacyPackages` is the standard way to access packages in flakes.
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      # ── Packages ─────────────────────────────────────────────────────────
      # `nix build`           → builds the default package (the Python app)
      # `nix build .#dockerImage` → builds the Docker image tarball
      packages.${system} = {
        # The Python application derivation (from default.nix)
        default = import ./default.nix { inherit pkgs; };

        # The Docker image tarball (from docker.nix)
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      # ── Development shell ─────────────────────────────────────────────────
      # `nix develop` drops you into a shell with Python + all dependencies.
      # This replaces the Lab 1 workflow:
      #   Lab 1:  python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
      #   Lab 18: nix develop   (same environment on every machine, every time)
      #
      # The shell is reproducible: same flake.lock = same Python version,
      # same package versions, same build tools — guaranteed.
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          # Exact Python version pinned by nixpkgs revision in flake.lock
          python3

          # Runtime dependencies (same as propagatedBuildInputs in default.nix)
          python3Packages.fastapi
          python3Packages.uvicorn
          python3Packages.python-json-logger
          python3Packages.prometheus-fastapi-instrumentator
          python3Packages.prometheus-client

          # Development tools
          python3Packages.pytest
          python3Packages.httpx

          # Nix tooling for working with the flake
          nixpkgs-fmt   # Nix code formatter
        ];

        # Shell hook: print environment info when entering the dev shell
        shellHook = ''
          echo "╔══════════════════════════════════════════════════════╗"
          echo "║  DevOps Info Service — Nix Development Shell         ║"
          echo "╠══════════════════════════════════════════════════════╣"
          echo "║  Python:  $(python --version)                        "
          echo "║  FastAPI: $(python -c 'import fastapi; print(fastapi.__version__)' 2>/dev/null || echo 'not found')"
          echo "║  Uvicorn: $(python -c 'import uvicorn; print(uvicorn.__version__)' 2>/dev/null || echo 'not found')"
          echo "╠══════════════════════════════════════════════════════╣"
          echo "║  Run app:  python app.py                             ║"
          echo "║  Tests:    pytest                                     ║"
          echo "╚══════════════════════════════════════════════════════╝"
        '';
      };

      # ── Apps ─────────────────────────────────────────────────────────────
      # `nix run` shortcut to run the service directly
      apps.${system}.default = {
        type    = "app";
        program = "${self.packages.${system}.default}/bin/devops-info-service";
      };
    };
}
