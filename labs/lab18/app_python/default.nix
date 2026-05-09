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
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service

    # Make the script executable and wrap it so Python and Flask are on PYTHONPATH
    chmod +x $out/bin/devops-info-service
    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH" \
      --set PATH "${pkgs.python3}/bin:$PATH"
  '';

  # Skip tests during Nix build (they require network / running server)
  doCheck = false;

  meta = with pkgs.lib; {
    description = "DevOps course info service — Flask-based Python application";
    license = licenses.mit;
    maintainers = [];
  };
}
