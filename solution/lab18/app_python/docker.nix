{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [
    app
    pkgs.cacert
  ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "RELEASE_VERSION=nix-container-1.0.0"
      "VISITS_FILE=/tmp/devops-info-service/visits"
    ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
    Labels = {
      "org.opencontainers.image.title" = "devops-info-service-nix";
      "org.opencontainers.image.description" = "Reproducible Nix dockerTools build for DevOps Core Lab 18";
      "org.opencontainers.image.version" = "1.0.0";
    };
  };

  created = "1970-01-01T00:00:01Z";
}
