# Lab 18 — reproducible OCI image tarball via dockerTools (compare with repo-root Dockerfile).
# Build: `nix-build docker.nix`   Load: `docker load < result`

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
    ExposedPorts = { "5000/tcp" = { }; };
    WorkingDir = "/";
  };

  # Fixed timestamp — required for bit-reproducible image tarballs (see lab).
  created = "1970-01-01T00:00:01Z";
}
