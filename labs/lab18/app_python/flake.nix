{
  description = "DevOps Info Service - Reproducible Build with Nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        packages = {
          default = import ./default.nix { inherit pkgs; };
          dockerImage = import ./docker.nix { inherit pkgs; };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs.python3Packages; [
            pkgs.python3
            fastapi
            uvicorn
            python-json-logger
            prometheus-client
          ];
        };
      });
}
