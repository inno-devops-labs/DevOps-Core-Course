{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [
    app
  ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "5002/tcp" = {};
    };
    Env = [
      "HOST=0.0.0.0"
      "PORT=5002"
      "SERVICE_NAME=devops-info-service"
      "SERVICE_VERSION=1.0.0"
      "VISITS_FILE=/tmp/devops-info-service-visits"
    ];
  };

  created = "1970-01-01T00:00:01Z";
}
