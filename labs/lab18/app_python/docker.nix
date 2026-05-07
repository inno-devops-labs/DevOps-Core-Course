{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";
  created = "1970-01-01T00:00:01Z";

  contents = [
    app
    pkgs.cacert
  ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=8000"
      "APP_ENV=nix-container"
      "APP_REGION=lab18"
      "VISITS_FILE=/tmp/devops-info-service/visits"
    ];
    ExposedPorts = {
      "8000/tcp" = {};
    };
  };
}
