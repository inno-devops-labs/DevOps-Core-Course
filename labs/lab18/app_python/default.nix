{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3;
  deps = with pkgs.python3Packages; [
    fastapi
    uvicorn
  ];
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  buildInputs = [ python ] ++ deps;

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    chmod +x $out/bin/devops-info-service
    
    sed -i '1i#!/usr/bin/env python3' $out/bin/devops-info-service
  '';
}