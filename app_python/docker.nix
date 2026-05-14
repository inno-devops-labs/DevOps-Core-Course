# Nix Docker image definition using dockerTools
# Lab 18 - Task 2: Reproducible Docker Images
#
# This creates a reproducible Docker image from the Nix-built application
#
# Key concepts:
# - buildLayeredImage: Creates efficient layered Docker images
# - contents: Packages/derivations to include in the image
# - config.Cmd: Default command to run when container starts
# - created: Timestamp for reproducibility (fixed, not "now")
#
# Why this is reproducible:
# - No base image dependency (builds from scratch)
# - Fixed timestamp (created = "1970-01-01T00:00:01Z")
# - Content-addressable layers (same content = same hash)
# - All dependencies pinned via nixpkgs

{ pkgs ? import <nixpkgs> {} }:

let
  # Import the application derivation from default.nix
  # This ensures we use the exact same build as in Task 1
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  # Image name (used when loading into Docker)
  name = "devops-info-service-nix";
  
  # Image tag
  tag = "1.0.0";

  # Contents to include in the image
  # This includes the app and ALL its dependencies (transitively!)
  # Nix automatically includes everything needed to run the app
  contents = [ 
    app
    pkgs.bash  # Include bash for any shell scripts
    pkgs.cacert  # Include CA certificates for HTTPS requests
  ];

  # Docker configuration (equivalent to Dockerfile instructions)
  config = {
    # Equivalent to CMD in Dockerfile
    # Uses the wrapped script from the Nix derivation
    Cmd = [ "${app}/bin/devops-info-service" ];
    
    # Equivalent to EXPOSE in Dockerfile
    ExposedPorts = {
      "5000/tcp" = {};
    };
    
    # Working directory (optional, Nix apps don't really need this)
    WorkingDir = "/app";
    
    # Environment variables (optional)
    Env = [
      "PYTHONUNBUFFERED=1"
      "PORT=5000"
    ];
  };

  # CRITICAL: Fixed timestamp for reproducibility
  # Using "now" would break reproducibility (different hash each build)
  # This is the key difference from traditional Dockerfiles!
  created = "1970-01-01T00:00:01Z";

  # Optional: Add labels for metadata
  extraLabels = {
    "org.opencontainers.image.title" = "DevOps Info Service";
    "org.opencontainers.image.description" = "FastAPI service built with Nix";
    "org.opencontainers.image.version" = "1.0.0";
    "org.opencontainers.image.source" = "https://github.com/course-repo";
  };
}
