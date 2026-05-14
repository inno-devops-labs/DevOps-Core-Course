{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi
    uvicorn
    prometheus-client
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";
  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let base = baseNameOf path; in
      !(builtins.elem base [ "result" "default.nix" "docker.nix" "flake.nix" "flake.lock" ])
      && !(pkgs.lib.hasPrefix "result-" base)
      && !(pkgs.lib.hasSuffix ".pyc" base)
      && base != "__pycache__";
  };

  nativeBuildInputs = [ pkgs.makeWrapper ];
  buildInputs = [ pythonEnv ];

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/share/devops-info-service $out/bin

    cp app.py config.py metrics.py $out/share/devops-info-service/
    cp -r routes services models $out/share/devops-info-service/

    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --set PYTHONDONTWRITEBYTECODE 1

    runHook postInstall
  '';
}
