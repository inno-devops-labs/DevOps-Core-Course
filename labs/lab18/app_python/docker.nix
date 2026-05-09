{ pkgs ? import <nixpkgs> {} }:

let
  # Import the Python application derivation from Task 1
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  # Image name and tag
  name = "devops-info-service-nix";
  tag = "1.0.0";

  # Packages to include in the image
  # - app: our Python application with all its dependencies
  # - busybox: provides basic shell utilities (optional, useful for debugging)
  contents = [ app pkgs.busybox ];

  # Container configuration (equivalent to Dockerfile CMD / EXPOSE)
  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
    ];
  };

  # Fixed timestamp for reproducibility — DO NOT use "now"!
  # Using epoch+1s ensures the image hash is identical across builds.
  created = "1970-01-01T00:00:01Z";
}
