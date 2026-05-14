{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
    prometheus-client
  ];

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  installPhase = ''
    mkdir -p $out/bin
    mkdir -p $out/share/devops-info-service

    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${pkgs.python3}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}