{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi
    uvicorn
    python-json-logger
    prometheus-client
    pydantic
    starlette
  ]);

  app = pkgs.stdenv.mkDerivation {
    pname = "devops-info-service";
    version = "1.0.0";

    src = ./.;

    installPhase = ''
      mkdir -p $out/app

      cp -r ./* $out/app/
    '';
  };

in pkgs.dockerTools.buildImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  copyToRoot = [
    pythonEnv
    app
  ];

  config = {
    Cmd = [
      "${pythonEnv}/bin/python"
      "-m"
      "uvicorn"
      "app:app"
      "--host"
      "0.0.0.0"
      "--port"
      "5001"
      "--app-dir"
      "/app"
    ];

    ExposedPorts = {
      "5001/tcp" = {};
    };
  };
}