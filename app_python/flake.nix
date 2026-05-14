# Nix Flake for DevOps Info Service
# Lab 18 - Bonus Task: Modern Nix with Flakes
#
# Flakes provide:
# - Automatic dependency locking via flake.lock
# - Standardized project structure
# - Better reproducibility across time
# - Easier sharing and collaboration
#
# Comparison with Lab 10 (Helm):
# - Helm values.yaml pins image versions (e.g., tag: "1.0.0")
# - Nix Flakes pin ALL dependencies (nixpkgs, Python packages, etc.)
# - Flakes provide stronger reproducibility guarantees

{
  description = "DevOps Info Service - Reproducible Build with Nix Flakes";

  inputs = {
    # Pin exact nixpkgs version for reproducibility
    # This is similar to pinning image tag in Helm values.yaml (Lab 10)
    # but applies to ALL dependencies, not just container images
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    
    # Optional: flake-utils for multi-system support
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # Packages that can be built with this flake
        packages = {
          # Default package (built with `nix build`)
          default = pkgs.callPackage ./default.nix { };
          
          # Docker image package (built with `nix build .#dockerImage`)
          dockerImage = pkgs.callPackage ./docker.nix { };
        };

        # Development shell with all dependencies
        # Enter with `nix develop` or `nix-shell`
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python313
            python313Packages.fastapi
            python313Packages.uvicorn
            python313Packages.prometheus-client
            python313Packages.pytest
            python313Packages.flake8
            # Nix tools for building
            nix
            docker
          ];
          
          # Shell hook to set up environment
          shellHook = ''
            echo "DevOps Info Service development environment"
            echo "Python: $(python --version)"
            echo "Run 'python -m uvicorn app:app --reload' to start dev server"
          '';
        };

        # Apps that can be run with `nix run`
        apps = {
          default = {
            type = "app";
            program = "${self.packages.${system}.default}/bin/devops-info-service";
          };
        };
      }
    );
}
