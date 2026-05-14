{ pkgs ? import <nixpkgs> {} }:

let
  # Bundle the interpreter together with all dependencies so PYTHONPATH is
  # automatically resolved and no wrapProgram (which embeds the build-host
  # bash path) is needed. This makes the derivation safe for cross-building
  # from aarch64-darwin to aarch64-linux.
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    flask
    python-json-logger
    prometheus-client
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  installPhase = ''
    mkdir -p $out/bin
    echo "#!${pythonEnv}/bin/python3" > $out/bin/devops-info-service
    cat app.py >> $out/bin/devops-info-service
    chmod +x $out/bin/devops-info-service
  '';
}
