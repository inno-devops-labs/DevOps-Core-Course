# default.nix — Nix derivation for DevOps Info Service (Python/Flask)
#
# This file describes how to build the application in a pure, reproducible
# Nix sandbox. Every input (Python version, Flask, prometheus-client) is
# content-addressed, so the same derivation always produces the same output.

{ pkgs ? import <nixpkgs> {} }:

let
  # Build a self-contained Python interpreter that already has every
  # dependency on its PYTHONPATH.  No pip, no venv, no network access.
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    flask              # web framework used by app.py
    prometheus-client  # /metrics endpoint
  ]);
in

pkgs.stdenv.mkDerivation {
  pname   = "devops-info-service";
  version = "1.0.0";

  # src points to the current directory; Nix hashes it and includes the hash
  # in the store path, so any source change produces a new derivation.
  src = ./.;

  # makeWrapper creates thin wrapper scripts that set environment variables
  # before exec-ing the real binary.
  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    # $out is the Nix store path assigned to this derivation, e.g.
    # /nix/store/<hash>-devops-info-service-1.0.0
    mkdir -p $out/bin $out/lib/devops-info-service

    # Copy the application source into the store
    cp app.py $out/lib/devops-info-service/app.py

    # Create an executable wrapper: running $out/bin/devops-info-service
    # invokes `python3 .../app.py`.  The pythonEnv already contains Flask
    # and prometheus-client, so no PYTHONPATH manipulation is needed.
    makeWrapper ${pythonEnv}/bin/python3 $out/bin/devops-info-service \
      --add-flags "$out/lib/devops-info-service/app.py"
  '';

  meta = {
    description = "DevOps course info service — reproducible Nix build";
  };
}
