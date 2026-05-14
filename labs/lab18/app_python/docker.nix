{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag  = "1.0.0";

  # The entire Nix closure (app + all its dependencies) is included as
  # content-addressable layers.  No base OS image is needed.
  contents = [ app pkgs.cacert ];

  config = {
    # Entrypoint: the wrapper script produced by default.nix
    Cmd = [ "${app}/bin/devops-info-service" ];

    ExposedPorts = {
      "8000/tcp" = {};
    };

    # Environment variables the app reads at runtime
    Env = [
      "HOST=0.0.0.0"
      "PORT=8000"
      "SERVICE_NAME=devops-info-service"
      "SERVICE_VERSION=1.0.0"
    ];
  };

  # ─── CRITICAL FOR REPRODUCIBILITY ───────────────────────────────────────
  # Using "now" would embed the build timestamp and break reproducibility.
  # A fixed epoch timestamp guarantees bit-for-bit identical images on every
  # machine, every time, with the same inputs.
  created = "1970-01-01T00:00:01Z";
}
