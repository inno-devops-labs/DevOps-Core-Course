{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";
  contents = [
    app
    pkgs.bash
    pkgs.coreutils
  ];
  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "VISITS_FILE_PATH=/tmp/devops-info-service-visits"
    ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
  };
  created = "1970-01-01T00:00:01Z";
}
