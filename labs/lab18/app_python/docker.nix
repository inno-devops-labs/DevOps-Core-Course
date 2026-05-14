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

  extraCommands = ''
    mkdir -p tmp
    chmod 1777 tmp
  '';

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "8000/tcp" = {};
    };
    Env = [
      "HOST=0.0.0.0"
      "PORT=8000"
      "VISITS_FILE=/tmp/devops-info-service-visits"
    ];
    WorkingDir = "/tmp";
  };

  created = "1970-01-01T00:00:01Z";
}
