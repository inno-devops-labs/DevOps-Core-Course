{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi
    uvicorn
    python-json-logger
    prometheus-fastapi-instrumentator
    prometheus-client
  ]);

  appSrc = pkgs.runCommand "devops-info-service-src" {} ''
    mkdir -p $out/app
    cp ${./app.py} $out/app/app.py
  '';
in

pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service";
  tag = "1.0.0";

  created = "1970-01-01T00:00:01Z";

  contents = [
    pythonEnv
    appSrc
    pkgs.coreutils
    pkgs.bash
  ];

  config = {
    Cmd = [
      "${pythonEnv}/bin/uvicorn"
      "app:app"
      "--host"
      "0.0.0.0"
      "--port"
      "8000"
    ];

    Env = [
      "PYTHONPATH=${appSrc}/app"
      "HOST=0.0.0.0"
      "PORT=8000"
      "DEBUG=False"
      "VISITS_FILE=/tmp/visits"
    ];

    ExposedPorts = {
      "8000/tcp" = {};
    };

    WorkingDir = "${appSrc}/app";

    Labels = {
      "org.opencontainers.image.title" = "devops-info-service";
      "org.opencontainers.image.version" = "1.0.0";
      "org.opencontainers.image.description" = "DevOps Info Service built reproducibly with Nix";
      "build.tool" = "nix-dockerTools";
    };
  };

  maxLayers = 120;
}