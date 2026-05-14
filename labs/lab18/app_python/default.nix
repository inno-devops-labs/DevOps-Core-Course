{ pkgs ? import <nixpkgs> {} }:

let
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
    mkdir -p $out/lib

    cp app.py $out/lib/app.py

    cat > $out/bin/devops-info-service <<EOF
#!/bin/sh
exec ${pythonEnv}/bin/python $out/lib/app.py
EOF

    chmod +x $out/bin/devops-info-service
  '';
}