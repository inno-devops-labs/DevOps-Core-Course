# Lab 18 Task 2 — reproducible OCI image via dockerTools (fixed image timestamp).
{ pkgs ? import <nixpkgs> { } }:
let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [ app ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "5000/tcp" = { };
    };
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
    ];
  };

  # Required for bit-reproducible tarballs (avoid "now").
  created = "1970-01-01T00:00:01Z";
}
