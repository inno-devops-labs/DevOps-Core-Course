{
  description = "DevOps Info Service - reproducible Lab 18 Nix build";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      python = pkgs.python313;
      pythonDeps = with python.pkgs; [
        flask
        prometheus-client
        python-json-logger
        pytest
        pytest-cov
        ruff
      ];
    in
    {
      packages.${system} = {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      apps.${system}.default = {
        type = "app";
        program = "${self.packages.${system}.default}/bin/devops-info-service";
      };

      devShells.${system}.default = pkgs.mkShell {
        packages = [ python ] ++ pythonDeps;

        VISITS_FILE = "/tmp/devops-info-service/visits";
        APP_CONFIG_PATH = "/tmp/devops-info-service/config.json";
        APP_NAME = "devops-info-service";
        APP_ENV = "nix-dev-shell";
        LOG_LEVEL = "INFO";
        PORT = "5000";

        shellHook = ''
          echo "Lab 18 dev shell: Python ${python.version}, Flask, prometheus-client, pytest, and ruff are available."
        '';
      };
    };
}
