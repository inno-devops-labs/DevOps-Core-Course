{ pkgs ? import <nixpkgs> {} }:
let
  lib = pkgs.lib;
  pythonEnv = pkgs.python313.withPackages (ps: with ps; [
    blinker
    click
    flask
    itsdangerous
    jinja2
    markupsafe
    werkzeug
  ]);
  srcClean = lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let
        relPath = lib.removePrefix (toString ./. + "/") (toString path);
      in
        # Exclude runtime / local artifacts that can change between runs
        !(relPath == "data/visits"
          || lib.hasPrefix "result" relPath
          || lib.hasPrefix "venv1" relPath
          || lib.hasPrefix "venv2" relPath
          || lib.hasPrefix ".venv" relPath
          || lib.hasPrefix "__pycache__" relPath
          || lib.hasPrefix ".pytest_cache" relPath);
  };
in pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0";

  src = srcClean;

  nativeBuildInputs = [pkgs.makeWrapper];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/.devops-info-service

    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/bin/.devops-info-service" \
  '';
}
