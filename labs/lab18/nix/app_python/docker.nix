{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
  
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    flask
    prometheus-client
    psutil
    pyyaml
    python-json-logger
  ]);

  rootEnv = pkgs.buildEnv {
    name = "root-env";
    paths = [
      pythonEnv
      app
    ];
    pathsToLink = [
      "/bin"
      "/lib"
      "/libexec"
    ];
    ignoreCollisions = true;
  };
  
in pkgs.dockerTools.buildImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";
  
  copyToRoot = rootEnv;
  
  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = { "5050/tcp" = {}; };
    WorkingDir = "/app";
    Env = [
      "PYTHONUNBUFFERED=1"
    ];
  };
  
  extraCommands = ''
    mkdir -p data app
  '';
}
