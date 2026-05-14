{
  description = "DevOps Info Service — Lab 18 reproducible build with Nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        app = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      in
      {
        packages = {
          default = app;
          devops-info-service = app;
          dockerImage = dockerImage;
        };

        apps.default = {
          type = "app";
          program = "${app}/bin/devops-info-service";
        };

        devShells.default = pkgs.mkShell {
          name = "devops-info-service-dev";
          buildInputs = with pkgs; [
            python313
            python313Packages.fastapi
            python313Packages.uvicorn
            python313Packages.pydantic
            python313Packages.pydantic-settings
            python313Packages.prometheus-client
            python313Packages.python-json-logger
            python313Packages.pytest
            python313Packages.httpx
            ruff
            uv
          ];
          shellHook = ''
            echo "Lab 18 dev shell — python $(python3 --version)"
            echo "Run: python -m app"
          '';
        };

        checks.build = app;
      });
}
