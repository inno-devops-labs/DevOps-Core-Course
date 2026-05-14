# Nix Docker image for DevOps Info Service.
# Build with:  nix-build docker.nix
# Load with:   docker load < result
# Run with:    docker run -p 5000:5000 devops-info-service-nix:1.0.0
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag  = "1.0.0";

  # Include the app and basic POSIX utilities (ls, sh, etc.) for debugging.
  contents = [ app pkgs.coreutils pkgs.bash ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];

    ExposedPorts = {
      "5000/tcp" = {};
    };

    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "PYTHONUNBUFFERED=1"
    ];
  };

  # CRITICAL: use a fixed timestamp — "now" would change on every build,
  # breaking bit-for-bit reproducibility.
  # 1970-01-01T00:00:01Z is the conventional epoch+1 for Nix Docker images.
  created = "1970-01-01T00:00:01Z";
}
