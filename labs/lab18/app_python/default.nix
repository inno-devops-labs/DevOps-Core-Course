{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    flask
    prometheus-client
  ]);
in
pkgs.stdenvNoCC.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";
  src = pkgs.lib.cleanSource ./.;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/app $out/bin
    cp -r . $out/app

    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --set DATA_DIR /tmp/devops-info-service-data \
      --set VISITS_FILE /tmp/devops-info-service-data/visits \
      --add-flags "$out/app/app.py"

    runHook postInstall
  '';
}
