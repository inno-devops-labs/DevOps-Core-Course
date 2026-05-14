# docker.nix — Reproducible Docker image for DevOps Info Service
#
# Uses Nix's dockerTools to produce a container image that is
# bit-for-bit identical every time it is built.  There is no base image
# pulled from Docker Hub; the image content is assembled from the Nix store.

{ pkgs ? import <nixpkgs> {} }:

let
  # Reuse the exact same derivation from Task 1.
  app = import ./default.nix { inherit pkgs; };
in

pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag  = "1.0.0";

  # contents lists every derivation that should be present in the image.
  # Nix computes the minimal closure — only what app actually needs.
  contents = [ app pkgs.coreutils ];

  config = {
    # The command Docker runs when the container starts.
    Cmd = [ "${app}/bin/devops-info-service" ];

    ExposedPorts = {
      "5000/tcp" = {};
    };

    # Environment variables the application reads at runtime.
    Env = [
      "PORT=5000"
      "HOST=0.0.0.0"
      "VISITS_FILE=/data/visits"
      "PYTHONDONTWRITEBYTECODE=1"
      "PYTHONUNBUFFERED=1"
    ];
  };

  # CRITICAL: "now" would embed the current timestamp and break
  # reproducibility.  A fixed epoch value ensures the tarball hash is
  # identical across builds.
  created = "1970-01-01T00:00:01Z";
}
