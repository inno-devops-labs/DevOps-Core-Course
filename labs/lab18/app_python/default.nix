{ pkgs ? import <nixpkgs> { } }:

let
  pythonEnv = pkgs.python3.withPackages (ps: [
    ps.flask
    ps."prometheus-client"
    ps."python-json-logger"
  ]);
in
pkgs.stdenvNoCC.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";

  src = builtins.path {
    path = ./.;
    name = "devops-info-service-src";
    filter = path: _type:
      let b = baseNameOf path; in b == "app.py" || b == "requirements.txt";
  };

  nativeBuildInputs = [ pkgs.makeWrapper ];

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall
    mkdir -p $out/lib
    cp app.py $out/lib/app.py
    mkdir -p $out/bin
    makeWrapper ${pythonEnv}/bin/python3 $out/bin/devops-info-service \
      --add-flags "$out/lib/app.py" \
      --chdir "$out/lib"
    runHook postInstall
  '';

  meta = {
    description = "DevOps course info service (Flask)";
    mainProgram = "devops-info-service";
  };
}
