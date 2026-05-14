{
  description = "DevOps Info Service reproducible build with Nix Flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [
        "aarch64-darwin"
        "x86_64-linux"
        "aarch64-linux"
      ];

      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = import ./default.nix { inherit pkgs; };
          dockerImage = import ./docker.nix { inherit pkgs; };
        });

      apps = forAllSystems (system:
        {
          default = {
            type = "app";
            program = "${self.packages.${system}.default}/bin/devops-info-service";
          };
        });

      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          python = pkgs.python313;
          pythonPackages = pkgs.python313Packages;
        in
        {
          default = pkgs.mkShell {
            packages = [
              python
              pythonPackages.fastapi
              pythonPackages.uvicorn
              pythonPackages.prometheus-client
              pkgs.curl
            ];

            shellHook = ''
              export DATA_DIR="$PWD/.nix-dev/data"
              export CONFIG_PATH="$PWD/.nix-dev/config/config.json"
              export APP_ENV="nix-flake-dev"
              export LOG_LEVEL="debug"
              export RELEASE_VERSION="1.0.0-flake"

              mkdir -p "$DATA_DIR" "$(dirname "$CONFIG_PATH")"

              echo "Nix flake dev shell ready"
              echo "Python: $(python --version)"
              echo "DATA_DIR=$DATA_DIR"
            '';
          };
        });
    };
}
