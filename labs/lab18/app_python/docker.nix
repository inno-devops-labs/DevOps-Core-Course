{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };

  pythonPackages = pkgs.python313Packages;

  pythonPath = pythonPackages.makePythonPath [
    pythonPackages.fastapi
    pythonPackages.uvicorn
    pythonPackages.prometheus-client
  ];
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [
    app
    pythonPackages.uvicorn
    pythonPackages.fastapi
    pythonPackages.prometheus-client
    pkgs.bash
    pkgs.coreutils
  ];

  config = {
    Cmd = [
      "${pythonPackages.uvicorn}/bin/uvicorn"
      "app:app"
      "--host"
      "0.0.0.0"
      "--port"
      "5000"
      "--no-access-log"
    ];

    ExposedPorts = {
      "5000/tcp" = {};
    };

    Env = [
      "PYTHONPATH=${app}/lib/devops-info-service:${pythonPath}"
      "DATA_DIR=/tmp/devops-info-service-data"
      "CONFIG_PATH=/tmp/devops-info-service-config/config.json"
      "APP_ENV=nix-docker"
      "LOG_LEVEL=info"
      "RELEASE_VERSION=1.0.0"
    ];

    WorkingDir = "/";
  };

  created = "1970-01-01T00:00:01Z";
}
