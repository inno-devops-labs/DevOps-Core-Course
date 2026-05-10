{
  description = "DevOps Info Service — reproducible build with Nix Flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        app = import ./default.nix { inherit pkgs; };
      in
      {
        packages = {
          default = app;
          dockerImage = import ./docker.nix { inherit pkgs; };
        };

        apps.default = {
          type = "app";
          program = "${app}/bin/devops-info-service";
        };

        devShells.default = pkgs.mkShell {
          name = "devops-info-service-dev";
          packages = with pkgs.python3Packages; [
            pkgs.python3
            flask
            prometheus-client
            requests
            pytest
          ];
          shellHook = ''
            echo "devops-info-service dev shell"
            python --version
          '';
        };
      }
    );
}
