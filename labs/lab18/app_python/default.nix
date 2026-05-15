{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3.withPackages (ps: with ps; [
    fastapi
    uvicorn
  ]);
in

pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";

  src = ./.;

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  installPhase = ''
    mkdir -p $out/bin
    mkdir -p $out/share/devops-info-service

    cp app.py $out/share/devops-info-service/

    makeWrapper ${python}/bin/uvicorn $out/bin/devops-info-service \
      --add-flags "app:app" \
      --add-flags "--host" \
      --add-flags "0.0.0.0" \
      --add-flags "--port" \
      --add-flags "5000" \
      --chdir "$out/share/devops-info-service"
  '';
}
