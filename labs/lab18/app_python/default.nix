{ pkgs ? import <nixpkgs> {} }:

pkgs.python312Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python312Packages; [
    fastapi
    uvicorn
    pydantic
    python-json-logger
    prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/lib $out/bin
    cp app.py $out/lib/app.py
    cp metrics.py $out/lib/metrics.py

    makeWrapper ${pkgs.python312}/bin/python3 $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$out/lib:$PYTHONPATH" \
      --add-flags "-m" \
      --add-flags "uvicorn" \
      --add-flags "app:app" \
      --add-flags "--host" \
      --add-flags "0.0.0.0" \
      --add-flags "--port" \
      --add-flags "5000"
  '';
}
