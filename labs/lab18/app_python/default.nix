{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: [
    ps.fastapi
    ps.uvicorn
    ps.psutil
    ps.python-json-logger
    ps.prometheus-client
  ]);
in
pkgs.stdenvNoCC.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";

  src = ./.;

  dontUnpack = true;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall
    mkdir -p $out/bin

    cat > $out/bin/devops-info-service <<EOF
#!${pkgs.bash}/bin/bash
exec ${pythonEnv}/bin/python ${./app.py}
EOF

    chmod +x $out/bin/devops-info-service
    runHook postInstall
  '';
}
