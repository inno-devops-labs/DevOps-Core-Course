{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [ app ];

  extraCommands = ''
    mkdir -p tmp
    chmod 1777 tmp
  '';

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "DEBUG=False"
      "APP_NAME=devops-info-service"
      "APP_ENV=nix-docker"
      "LOG_LEVEL=INFO"
      "VISITS_FILE=/tmp/devops-info-service/visits"
      "APP_CONFIG_PATH=/tmp/devops-info-service/config.json"
    ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
    WorkingDir = "/tmp";
    Labels = {
      "org.opencontainers.image.title" = "DevOps Info Service";
      "org.opencontainers.image.description" = "Reproducible image built with Nix dockerTools";
      "org.opencontainers.image.version" = "1.0.0";
    };
  };

  created = "1970-01-01T00:00:01Z";
}
