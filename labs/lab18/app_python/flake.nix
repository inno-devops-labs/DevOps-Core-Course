{
  description = "DevOps Info Service - Lab 18 reproducible builds";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      app = import ./default.nix { inherit pkgs; };
      dockerImage = import ./docker.nix { inherit pkgs; };
    in {
      packages.${system} = {
        default = app;
        dockerImage = dockerImage;
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python313
          python313Packages.flask
          python313Packages.werkzeug
          python313Packages.gunicorn
          python313Packages.python-json-logger
          python313Packages.prometheus-client
        ];
      };
    };
}