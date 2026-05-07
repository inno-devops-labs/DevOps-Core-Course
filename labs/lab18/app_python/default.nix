{ pkgs ? import <nixpkgs> {} }:

pkgs.python312Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;
  format = "other";

  propagatedBuildInputs = with pkgs.python312Packages; [
    flask
    prometheus-client
    portalocker
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  doCheck = false;

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}