{
  description = "DevOps Info Service reproducible build with Nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs = { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      app = import ./default.nix { inherit pkgs; };
      dockerImage = import ./docker.nix { inherit pkgs; };
    in
    {
      packages.${system} = {
        default = app;
        dockerImage = dockerImage;
      };

      apps.${system}.default = {
        type = "app";
        program = "${app}/bin/devops-info-service";
      };

      devShells.${system}.default = pkgs.mkShell {
        packages = [
          (pkgs.python313.withPackages (ps: with ps; [
            flask
            prometheus-client
            pytest
            pytest-cov
            python-dotenv
            python-json-logger
            requests
          ]))
        ];
      };
    };
}
