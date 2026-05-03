{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.1.0";

  contents = [ app pkgs.coreutils pkgs.bash ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "APP_NAME=devops-info-service"
      "APP_ENV=container"
      "PORT=5000"
      "HOST=0.0.0.0"
      "VISITS_FILE_PATH=/tmp/visits"
      "APP_CONFIG_PATH=${app}/share/devops-info-service/config/config.json"
    ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
  };

  created = "1970-01-01T00:00:01Z";
  fakeRootCommands = "";
}
