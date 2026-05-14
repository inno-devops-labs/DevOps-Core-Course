# Lab 18 Task 1 — reproducible DevOps Info Service (same app as Lab 1).
# Uses nixpkgs-pinned Python with Flask + prometheus-client from the package set
# (not PyPI at resolve time), so the closure is fixed for a given nixpkgs revision.
{ pkgs ? import <nixpkgs> { } }:
let
  pythonEnv = pkgs.python3.withPackages (
    ps: with ps; [
      flask
      prometheus-client
    ]
  );
in
pkgs.stdenvNoCC.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall
    mkdir -p $out/share/devops-info-service
    cp ${./app.py} $out/share/devops-info-service/app.py

    # Default visits file: writable without extra mounts (Docker/Nix run).
    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --set-default VISITS_FILE /tmp/devops-info-visits

    runHook postInstall
  '';

  meta = {
    description = "DevOps Info Service (Flask) — Lab 18 Nix package";
    mainProgram = "devops-info-service";
  };
}
