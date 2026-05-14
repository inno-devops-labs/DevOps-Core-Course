{ pkgs ? import <nixpkgs> {} }:

let
  # Import the application derivation from default.nix
  app = import ./default.nix { inherit pkgs; };
in

# Build a layered Docker image using Nix's dockerTools
# Key advantage: content-addressable layers, no timestamps by default
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  # Include the app and its minimal runtime dependencies
  # No base OS image needed - Nix provides exactly what's required
  contents = [
    app
    pkgs.coreutils  # For basic shell utilities inside the container
    pkgs.bash       # Required for the wrapper script
  ];

  config = {
    # Full path in the Nix store - reproducible and deterministic
    Cmd = [ "${app}/bin/devops-info-service" ];

    ExposedPorts = {
      "5000/tcp" = {};
    };

    Env = [
      "APP_HOST=0.0.0.0"
      "APP_PORT=5000"
      "DATA_DIR=/data"
    ];

    WorkingDir = "${app}/lib/devops-info-service";
  };

  # CRITICAL: Fixed timestamp makes the image reproducible
  # Using "now" would cause different hashes on each build
  created = "1970-01-01T00:00:01Z";
}
