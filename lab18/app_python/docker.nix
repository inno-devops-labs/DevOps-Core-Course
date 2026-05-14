{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag  = "1.0.0";

  # dockerTools computes one layer per unique store path in the closure.
  # Layers are content-addressed: identical content always produces the
  # same layer digest, enabling perfect remote caching.
  contents = [
    app
    pkgs.coreutils  # provides basic POSIX utilities inside the container
  ];

  config = {
    Cmd          = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = { "8080/tcp" = {}; };
    Env          = [ "VISITS_FILE=/tmp/devops-info-visits" ];
  };

  # Fixed epoch timestamp makes the image tarball bit-for-bit reproducible.
  # Using "now" would embed the build timestamp and break hash stability.
  created = "1970-01-01T00:00:01Z";
}
