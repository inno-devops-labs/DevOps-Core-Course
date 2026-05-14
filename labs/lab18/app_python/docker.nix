{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [
    app
    pkgs.bashInteractive
    pkgs.coreutils
  ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=5002"
      "VISITS_FILE=/tmp/devops-info-service-visits"
    ];
    ExposedPorts = {
      "5002/tcp" = {};
    };
  };

  created = "1970-01-01T00:00:01Z";
}
