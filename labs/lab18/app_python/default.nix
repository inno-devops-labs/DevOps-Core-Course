{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  # No setup.py — we handle installation manually
  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
    python-json-logger
    prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service

    # Wrap with Python interpreter and inject PYTHONPATH so imports resolve
    wrapProgram $out/bin/devops-info-service \
      --set PYTHONPATH "$PYTHONPATH" \
      --prefix PATH : "${pkgs.python3}/bin"
  '';
}
