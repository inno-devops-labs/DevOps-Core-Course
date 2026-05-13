{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-python-app-nix";
  tag = "1.0.0";

  contents = [ app pkgs.coreutils ];

  config = {
    Cmd = [ "${app}/bin/devops-python-app" ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
    WorkingDir = "/data";
  };

  created = "1970-01-01T00:00:01Z";
}
