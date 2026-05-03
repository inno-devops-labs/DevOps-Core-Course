{ pkgs ? import <nixpkgs> {} }:
let app = import ./default.nix { inherit pkgs; }; in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [app];

  config = {
    ExposedPorts = {
      "5000/tcp" = {};
    };
    Cmd = ["${app}/bin/devops-info-service"];
  };
  created = "1970-01-01T00:00:01Z";  # Reproducible timestamp
}
