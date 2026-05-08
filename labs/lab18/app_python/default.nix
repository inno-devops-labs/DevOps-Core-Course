{ pkgs ? import <nixpkgs> {} }:

let
  pythonWithPackages = pkgs.python3.withPackages (ps: with ps; [
    fastapi
    uvicorn
    starlette
    prometheus-client
    python-json-logger
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  buildInputs = [ pythonWithPackages ];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    chmod +x $out/bin/devops-info-service
    
    # Use python with packages baked in
    sed -i '1i#!${pythonWithPackages}/bin/python' $out/bin/devops-info-service
  '';
}