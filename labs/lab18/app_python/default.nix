{ pkgs ? import (builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/refs/heads/nixos-24.11.tar.gz";
  }) {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    flask
    python-dotenv
  ]);
in

pkgs.stdenv.mkDerivation {
  pname   = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin $out/lib
    cp $src/app.py $out/lib/app.py

    makeWrapper ${pythonEnv}/bin/python3 $out/bin/devops-info-service \
      --add-flags "$out/lib/app.py"
  '';

  meta = {
    description = "DevOps Info Service — Flask app built with Nix";
  };
}