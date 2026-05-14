{ pkgs ? import <nixpkgs> {} }:

let
  source = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let
        name = baseNameOf path;
      in
      ! (
        name == "result"
        || name == ".git"
        || name == "__pycache__"
        || pkgs.lib.hasSuffix ".pyc" name
      );
  };

  pythonEnv = pkgs.python313.withPackages (ps: with ps; [
    flask
    prometheus-client
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";
  src = source;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --set PORT 5002 \
      --set VISITS_FILE /tmp/devops-info-service-visits

    runHook postInstall
  '';
}
