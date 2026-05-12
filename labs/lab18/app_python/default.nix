{ pkgs ? import <nixpkgs> { } }:

let
  lib = pkgs.lib;
  srcRoot = ./.;
  appSrc = builtins.path {
    name = "devops-info-service-src";
    path = srcRoot;
    filter = path: _type:
      let
        rel = lib.removePrefix ((toString srcRoot) + "/") (toString path);
      in
      rel != "venv"
      && !(lib.hasPrefix "venv/" rel)
      && !(lib.hasPrefix ".pytest_cache" rel)
      && (baseNameOf path != "result");
  };
in
pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = appSrc;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  # No packaged pytest suite wired for this layout; runtime app only.
  doCheck = false;

  installPhase = ''
    mkdir -p $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${pkgs.python3Packages.python}/bin/python3 $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH" \
      --add-flags "$out/share/devops-info-service/app.py"
  '';
}
