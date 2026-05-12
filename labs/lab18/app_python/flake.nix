{
  description = "DevOps Info Service - reproducible Nix build for Lab 18";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs }:
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

      checks.${system}.default = app;

      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          python3
          python3Packages.flask
          python3Packages.prometheus-client
          python3Packages.pytest
        ];

        shellHook = ''
          export VISITS_FILE="$PWD/data/visits"
          echo "Lab 18 Nix shell: Python $(python --version)"
        '';
      };
    };
}
