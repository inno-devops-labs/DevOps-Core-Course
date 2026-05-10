{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  # No setup.py/pyproject.toml — use "other" format
  format = "other";

  # Runtime Python dependencies (equivalent to requirements.txt: Flask==3.1.0)
  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
  ];

  # Build-time tools: makeWrapper wraps the script with the correct Python + PYTHONPATH
  nativeBuildInputs = [ pkgs.makeWrapper ];

  # Custom install phase since there is no setup.py
  installPhase = ''
    mkdir -p $out/bin $out/lib

    # Copy the application source to lib
    cp app.py $out/lib/app.py

    # Create a launcher script that invokes Python explicitly
    cat > $out/bin/devops-info-service <<LAUNCHER
    #!/bin/sh
    exec ${pkgs.python3}/bin/python3 $out/lib/app.py "\$@"
    LAUNCHER
    chmod +x $out/bin/devops-info-service

    # Wrap the launcher so PYTHONPATH includes Flask and all dependencies
    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';

  # Skip tests during Nix build (they require network / running server)
  doCheck = false;

  meta = with pkgs.lib; {
    description = "DevOps course info service — Flask-based Python application";
    license = licenses.mit;
    maintainers = [];
  };
}
