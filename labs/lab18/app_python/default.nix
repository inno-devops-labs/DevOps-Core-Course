{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python313;
  pythonPackages = pkgs.python313Packages;

  pythonPath = pythonPackages.makePythonPath [
    pythonPackages.fastapi
    pythonPackages.uvicorn
    pythonPackages.prometheus-client
  ];
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";

  src = ./.;

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  installPhase = ''
    mkdir -p $out/lib/devops-info-service
    mkdir -p $out/bin

    cp app.py $out/lib/devops-info-service/app.py

    makeWrapper ${pythonPackages.uvicorn}/bin/uvicorn $out/bin/devops-info-service \
      --add-flags "app:app --host 0.0.0.0 --port 5005 --no-access-log" \
      --set PYTHONPATH "$out/lib/devops-info-service:${pythonPath}" \
      --set DATA_DIR "/tmp/devops-info-service-data" \
      --set CONFIG_PATH "/tmp/devops-info-service-config/config.json" \
      --set APP_ENV "nix" \
      --set LOG_LEVEL "info" \
      --set RELEASE_VERSION "1.0.0"
  '';

  meta = {
    description = "DevOps Info Service built reproducibly with Nix";
    mainProgram = "devops-info-service";
  };
}
