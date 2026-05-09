{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";
  doCheck = false;

  propagatedBuildInputs = [
    pkgs.python3Packages.fastapi
    pkgs.python3Packages.uvicorn
    pkgs.python3Packages."prometheus-client"
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/libexec $out/bin
    cp app.py $out/libexec/app.py

    # Wrapper runs the script with the correct interpreter and PYTHONPATH
    makeWrapper ${pkgs.python3}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/libexec/app.py" \
      --set PYTHONPATH "$PYTHONPATH"
  '';
}
