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
in

pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";

  src = ./.;

  buildInputs = [ pythonEnv ];

  installPhase = ''
    mkdir -p $out/app
    mkdir -p $out/bin

    cp -r ./* $out/app/

    cat > $out/bin/devops-info-service <<EOF
    #!/bin/sh
    exec ${pythonEnv}/bin/python -m uvicorn app:app \
      --host 0.0.0.0 \
      --port 5001 \
      --app-dir $out/app
    EOF

    chmod +x $out/bin/devops-info-service
  '';
}