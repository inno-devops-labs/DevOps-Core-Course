{
  description = "DevOps Info Service — reproducible build with Nix Flakes";

  inputs = {
    # Pin nixpkgs to a specific stable channel revision.
    # Changing this URL is the only way dependencies can ever change —
    # making the entire closure cryptographically locked.
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      # ── Platform ────────────────────────────────────────────────────────
      # This project runs on macOS Apple-Silicon (aarch64-darwin).
      # Swap for "x86_64-linux" on Linux / WSL2, or "x86_64-darwin" on Intel Mac.
      system = "aarch64-darwin";
      pkgs   = nixpkgs.legacyPackages.${system};
    in
    {
      # ── Buildable packages ───────────────────────────────────────────────
      packages.${system} = {
        # `nix build` or `nix build .#default`
        default = import ./default.nix { inherit pkgs; };

        # `nix build .#dockerImage`
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      # ── Development shell ────────────────────────────────────────────────
      # `nix develop` — drops you into an isolated shell with the exact
      # Python version and all runtime dependencies available, replacing
      # Lab 1's `python -m venv venv && pip install -r requirements.txt`.
      devShells.${system}.default = pkgs.mkShell {
        name = "devops-info-service-dev";

        packages = with pkgs; [
          (python3.withPackages (ps: with ps; [
            fastapi
            uvicorn
            prometheus-client
            python-json-logger
            httpx
            python-dotenv
            # dev/test extras
            pytest
            pytest-cov
          ]))
        ];

        shellHook = ''
          echo "🐍 DevOps Info Service dev shell (Python $(python3 --version | cut -d' ' -f2))"
          echo "   Run:  python main.py"
          echo "   Test: pytest"
        '';
      };

      # ── Formatter (optional) ─────────────────────────────────────────────
      formatter.${system} = pkgs.nixfmt-rfc-style;
    };
}
