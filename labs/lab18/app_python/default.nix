{ pkgs ? import <nixpkgs> {} }:

let
  pyPackages = pkgs.python314Packages;
in
pyPackages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";

  src = ./.;

  format = "other";

  propagatedBuildInputs = with pyPackages; [
    fastapi
    uvicorn
    python-json-logger
    prometheus-client
    python-dotenv
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    chmod +x $out/bin/devops-info-service

    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}
