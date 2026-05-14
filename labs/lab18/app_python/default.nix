{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication rec {
  pname = "devops-info-service";
  version = "1.0.0";

  src = ./.;
  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
    werkzeug
    gunicorn
    python-json-logger
    prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/lib/${pname}
    cp app.py $out/lib/${pname}/app.py

    makeWrapper ${pkgs.python3}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/lib/${pname}/app.py" \
      --set PYTHONUNBUFFERED 1 \
      --prefix PYTHONPATH : "$PYTHONPATH"

    runHook postInstall
  '';
}
