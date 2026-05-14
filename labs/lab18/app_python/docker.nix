{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    flask
    python-json-logger
    prometheus-client
  ]);

  app = pkgs.stdenv.mkDerivation {
    name = "app";
    src = ./.;

    installPhase = ''
      mkdir -p $out/lib
      cp app.py $out/lib/app.py
    '';
  };

in

pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [
    pythonEnv
    app
  ];

  config = {
    Cmd = [ "${pythonEnv}/bin/python" "${app}/lib/app.py" ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
  };

  created = "1970-01-01T00:00:01Z";
}
