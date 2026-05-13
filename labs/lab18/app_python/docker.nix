{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [ app pkgs.coreutils ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
    Env = [
      "PORT=5000"
      "HOST=0.0.0.0"
      "DEBUG=False"
    ];
  };

  # Fixed timestamp for reproducibility (NOT "now")
  created = "1970-01-01T00:00:01Z";
  maxLayers = 10;
}
