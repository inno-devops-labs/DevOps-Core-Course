{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    flask
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  installPhase = ''
    mkdir -p $out/bin
    
    cp app.py $out/bin/app.py
    chmod +x $out/bin/app.py
    
    cat > $out/bin/devops-info-service <<SCRIPT
#!/bin/bash
${pythonEnv}/bin/python $out/bin/app.py
SCRIPT
    
    chmod +x $out/bin/devops-info-service
  '';
}
