{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;
  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
    python-json-logger
    prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin $out/lib
    cp app.py $out/lib/devops-info-service.py

    makeWrapper ${pkgs.python3}/bin/python3 $out/bin/devops-info-service \
      --add-flags "$out/lib/devops-info-service.py" \
      --set PYTHONPATH "${pkgs.python3Packages.flask}/${pkgs.python3.sitePackages}:${pkgs.python3Packages.python-json-logger}/${pkgs.python3.sitePackages}:${pkgs.python3Packages.prometheus-client}/${pkgs.python3.sitePackages}"
  '';
}
