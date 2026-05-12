{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [ app ];

  extraCommands = ''
    mkdir -m 1777 -p tmp
  '';

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "DEBUG=false"
      "VISITS_FILE=/tmp/devops-info-visits"
      "PYTHONUNBUFFERED=1"
    ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
    WorkingDir = "/tmp";
    User = "1000:1000";
  };

  created = "1970-01-01T00:00:01Z";
}
