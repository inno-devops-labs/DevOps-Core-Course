{ pkgs ? import <nixpkgs> { } }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    flask
    prometheus-client
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ../app_python;

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin

    {
      echo "#!${pythonEnv}/bin/python3"
      cat app.py
    } > $out/bin/devops-info-service
    chmod +x $out/bin/devops-info-service

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service - Flask app rebuilt with Nix for reproducibility";
    license = licenses.mit;
    platforms = platforms.unix;
    mainProgram = "devops-info-service";
  };
}
