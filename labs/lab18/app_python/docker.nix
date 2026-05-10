{ pkgs ? import <nixpkgs> { } }:

# Lab 18 Task 2 — Reproducible Docker image via Nix `dockerTools`.
#
# Compared with the traditional Dockerfile in this directory (which is what
# Lab 02 used), this build:
#   - has no base image — only the closure of `app` is included
#   - has no embedded build timestamps (`created` is fixed below)
#   - is content-addressable: same source ⇒ same `result` tarball,
#     same `sha256sum result`, same image layer hashes — forever
#
# Build:   nix-build docker.nix
# Load:    docker load < result
# Run:     docker run -d -p 8080:8080 devops-info-service-nix:1.0.0

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  # `created` MUST NOT be "now" — that timestamps the image and breaks
  # reproducibility. Setting it to the Unix epoch makes the manifest
  # bit-for-bit identical across builds.
  created = "1970-01-01T00:00:01Z";

  # Everything that ends up on the image's filesystem.
  contents = [
    app
    # tiny userland for `docker exec` and probes — nothing else.
    pkgs.coreutils
    pkgs.bashInteractive
  ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "8080/tcp" = { };
    };
    Env = [
      "HOST=0.0.0.0"
      "PORT=8080"
      "DEBUG=False"
    ];
    Labels = {
      "org.opencontainers.image.source" = "https://github.com/AEZuraa/DevOps-Core-Course";
      "org.opencontainers.image.title" = "devops-info-service";
      "org.opencontainers.image.version" = "1.0.0";
    };
  };
}
