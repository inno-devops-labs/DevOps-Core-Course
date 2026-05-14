{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  copyToRoot = pkgs.buildEnv {
    name = "image-root";
    paths = [
      app
      pkgs.coreutils
      pkgs.bash
    ];
    pathsToLink = [ "/bin" "/lib" ];
  };

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "8000/tcp" = {};
    };
    Env = [
      "HOST=0.0.0.0"
      "PORT=8000"
      "PYTHONUNBUFFERED=1"
    ];
  };

  # Reproducible epoch timestamp — critical for bit-for-bit reproducibility
  created = "1970-01-01T00:00:01Z";
}
