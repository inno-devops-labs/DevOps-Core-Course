# flake.nix — Modern Nix Flake for DevOps Info Service
#
# A flake has two mandatory sections:
#   inputs  — external dependencies, pinned in flake.lock
#   outputs — what this project provides (packages, devShells, …)
#
# Unlike default.nix which uses a floating <nixpkgs> channel, a flake
# locks the exact nixpkgs revision in flake.lock, guaranteeing that builds
# produce the same result today, next year, and on any collaborator's machine.

{
  description = "DevOps Info Service — reproducible Nix Flake build";

  inputs = {
    # Pin to a specific NixOS release rather than an unstable channel.
    # The exact commit is recorded in flake.lock after running `nix flake update`.
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      # Target the Linux x86_64 platform used in WSL2.
      # Change to "x86_64-darwin" or "aarch64-darwin" on macOS.
      system = "x86_64-linux";
      pkgs   = nixpkgs.legacyPackages.${system};
    in
    {
      # --- Packages ---

      packages.${system} = {
        # `nix build` builds this by default
        default = import ./default.nix { inherit pkgs; };

        # `nix build .#dockerImage` builds the container image
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      # --- Development shell ---
      # `nix develop` drops into a shell with the exact Python and
      # dependencies declared below.  No manual venv setup required;
      # the environment is identical on every machine.

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python3
          python3Packages.flask
          python3Packages.prometheus-client
          python3Packages.pytest
        ];

        shellHook = ''
          echo "DevOps Info Service dev shell ready."
          echo "Python: $(python3 --version)"
          echo "Run: python3 app.py"
        '';
      };
    };
}
